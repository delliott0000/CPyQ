from __future__ import annotations

from asyncio import gather
from logging import ERROR
from typing import TYPE_CHECKING

from asyncpg import create_pool

from .company import Company
from .permissions import Permission, PermissionScope, PermissionType
from .quote import Quote
from .team import Team
from .user import User
from .utils import check_password, encrypt_password, log

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine, Iterable
    from typing import Any, Self, TypeVar

    from asyncpg import Connection, Pool, Record

    from .config import PostgresConfig

    T = TypeVar("T")
    QuoteT = TypeVar("QuoteT", bound=Quote)

__all__ = ("PostgreSQLClient",)


DUMMY_HASH = encrypt_password("my_dummy_password")


class PostgreSQLClient:
    def __init__(self, *, config: PostgresConfig):
        self.config = config
        self.__connection_pool: Pool | None = None

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(self, *_) -> None:
        await self.disconnect()

    @property
    def is_open(self) -> bool:
        return self.__connection_pool is not None and not self.__connection_pool.is_closing()

    def validate_ids(
        self,
        passed_ids: Iterable[int],
        found_ids: Iterable[int],
        /,
        *,
        context: str | None = None,
    ) -> None:
        missing_ids = set(passed_ids) - set(found_ids)
        if missing_ids:
            formatted_missing_ids = ", ".join(map(str, sorted(missing_ids)))
            formatted_context = context or "item"
            raise ValueError(
                f"Some of the requested {formatted_context} IDs were not found: {formatted_missing_ids}"
            )

    async def connect(self) -> None:
        if self.is_open:
            return

        config = self.config

        try:
            self.__connection_pool = await create_pool(
                host=config.host,
                port=config.port,
                database=config.database,
                user=config.user,
                password=config.password,
                min_size=config.min_pool_size,
                max_size=config.max_pool_size,
            )
            log(f"Connected to {config.database} as {config.user}.")
        except Exception as error:
            log(f"Failed to connect to {config.database} - {type(error).__name__}.", ERROR)
            raise

    async def disconnect(self) -> None:
        if not self.is_open:
            return

        config = self.config

        try:
            await self.__connection_pool.close()
            log(f"Disconnected from {config.database}.")
        except Exception as error:
            log(f"Failed to disconnect from {config.database} - {type(error).__name__}.", ERROR)

        self.__connection_pool = None

    async def make_call(self, func: Callable[[Connection], Coroutine[Any, Any, T]], /) -> T:
        if not self.is_open:
            raise RuntimeError("Postgres connection pool is closed.")

        async with self.__connection_pool.acquire() as connection:
            return await func(connection)

    async def fetch_one(self, query: str, *args: Any) -> Record | None:
        return await self.make_call(lambda connection: connection.fetchrow(query, *args))

    async def fetch_all(self, query: str, *args: Any) -> list[Record]:
        return await self.make_call(lambda connection: connection.fetch(query, *args))

    async def execute(self, query: str, *args: Any) -> str:
        return await self.make_call(lambda connection: connection.execute(query, *args))

    async def get_user(
        self,
        *,
        user_id: int | None = None,
        username: str | None = None,
        password: str | None = None,
        with_password: bool = True,
    ) -> User | None:
        if password is None and with_password is True:
            raise ValueError("Password is required.")
        elif user_id is not None:
            user_record = await self.fetch_one("SELECT * FROM users WHERE id = $1", user_id)
        elif username is not None:
            user_record = await self.fetch_one(
                "SELECT * FROM users WHERE username = $1", username
            )
        else:
            raise ValueError("Username or ID is required.")

        if user_record is None:
            if with_password:
                # Dummy check so we don't leak any info through query timing
                check_password(password, DUMMY_HASH)
            return None
        elif with_password and not check_password(password, user_record["password"]):
            return None

        team_assignments = await self.get_assignments(user_record["id"])
        team_ids = team_assignments.get(user_record["id"], [])
        teams = await self.get_teams(*team_ids)

        return User(user_record, frozenset(teams.values()))

    async def get_teams(self, *team_ids: int) -> dict[int, Team]:
        if not team_ids:
            return {}

        team_records = await self.fetch_all("SELECT * FROM teams WHERE id = ANY($1)", team_ids)

        company_ids = tuple(record["company_id"] for record in team_records)

        companies, permissions = await gather(
            self.get_companies(*company_ids), self.get_permissions(*team_ids)
        )

        teams = {
            record["id"]: Team(
                record, companies[record["company_id"]], frozenset(permissions[record["id"]])
            )
            for record in team_records
        }
        self.validate_ids(team_ids, teams.keys(), context="team")

        return teams

    async def get_companies(self, *company_ids: int) -> dict[int, Company]:
        if not company_ids:
            return {}

        company_records = await self.fetch_all(
            "SELECT * FROM companies WHERE id = ANY($1)", company_ids
        )

        companies = {record["id"]: Company(record) for record in company_records}
        self.validate_ids(company_ids, companies.keys(), context="company")

        return companies

    async def get_permissions(self, *team_ids: int) -> dict[int, list[Permission]]:
        if not team_ids:
            return {}

        permission_records = await self.fetch_all(
            "SELECT * FROM permissions WHERE team_id = ANY($1)", team_ids
        )

        permissions = {id_: [] for id_ in team_ids}

        for record in permission_records:
            permissions[record["team_id"]].append(
                Permission(
                    type=PermissionType(record["permission_type"]),
                    scope=PermissionScope(record["permission_scope"]),
                )
            )

        return permissions

    async def get_assignments(self, *ids: int, inverse: bool = False) -> dict[int, list[int]]:
        if not ids:
            return {}

        key_map = {False: "user_id", True: "team_id"}
        key = key_map[inverse]
        val = key_map[not inverse]

        assignment_records = await self.fetch_all(
            f"SELECT * FROM assignments WHERE {key} = ANY($1)", ids
        )

        assignments = {id_: [] for id_ in ids}

        for record in assignment_records:
            assignments[record[key]].append(record[val])

        return assignments

    async def get_quote(self, quote_id: int, /, *, cls: type[QuoteT] = Quote) -> QuoteT | None:
        quote_record = await self.fetch_one("SELECT * FROM quotes WHERE id = $1", quote_id)

        if quote_record is None:
            return None

        owner_id = quote_record["owner_id"]
        owner = await self.get_user(user_id=owner_id, with_password=False)

        return cls(quote_record, owner)
