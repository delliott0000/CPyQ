from __future__ import annotations

from asyncio import gather
from logging import ERROR
from typing import TYPE_CHECKING

from asyncpg import create_pool

from Common import log

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine, Iterable
    from typing import Any, Self, TypeVar

    from asyncpg import Connection, Pool

    from Common import PostgresConfig

    Json = dict[str, Any]
    T = TypeVar("T")

__all__ = ("PostgreSQLClient",)


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

    @staticmethod
    def deduplicate(ids: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(set(ids))

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
                user=config.username,
                password=config.password,
                min_size=config.min_connection_pool_size,
                max_size=config.max_connection_pool_size,
            )
            log(f"Connected to {config.database} as {config.username}.")
        except Exception as error:
            log(f"Failed to connect to {config.database}.", ERROR, error=error)
            raise

    async def disconnect(self) -> None:
        if not self.is_open:
            return

        config = self.config

        try:
            await self.__connection_pool.close()
            log(f"Disconnected from {config.database}.")
        except Exception as error:
            log(f"Failed to disconnect from {config.database}.", ERROR, error=error)

        self.__connection_pool = None

    async def make_call(self, func: Callable[[Connection], Coroutine[Any, Any, T]], /) -> T:
        if not self.is_open:
            raise RuntimeError("Postgres connection pool is closed.")

        async with self.__connection_pool.acquire() as connection:
            return await func(connection)

    async def fetch_one(self, query: str, /, *args: Any) -> Json | None:
        record = await self.make_call(lambda connection: connection.fetchrow(query, *args))
        return dict(record) if record is not None else None

    async def fetch_all(self, query: str, /, *args: Any) -> list[Json]:
        records = await self.make_call(lambda connection: connection.fetch(query, *args))
        return [dict(record) for record in records]

    async def execute(self, query: str, /, *args: Any) -> str:
        return await self.make_call(lambda connection: connection.execute(query, *args))

    async def get_user(self, username: str, /) -> Json | None:
        json = await self.fetch_one("SELECT * FROM users WHERE username = $1", username)

        if json is None:
            return None

        team_assignments = await self.get_assignments(json["id"])
        team_ids = team_assignments.get(json["id"], [])
        teams = await self.get_teams(*team_ids)

        return json | {"teams": list(teams.values())}

    async def get_users(self, *user_ids: int) -> dict[int, Json]:
        if not user_ids:
            return {}

        user_ids = self.deduplicate(user_ids)

        json_list = await self.fetch_all("SELECT * FROM users WHERE id = ANY($1)", user_ids)

        users = {json["id"]: json for json in json_list}
        user_keys = users.keys()

        assignments = await self.get_assignments(*user_keys)

        team_ids = (team_id for assignment in assignments.values() for team_id in assignment)

        teams = await self.get_teams(*team_ids)

        for user_id in user_keys:
            team_ids = assignments[user_id]
            user_teams = list(teams[team_id] for team_id in team_ids)
            users[user_id]["teams"] = user_teams

        self.validate_ids(user_ids, user_keys, context="user")

        return users

    async def get_teams(self, *team_ids: int) -> dict[int, Json]:
        if not team_ids:
            return {}

        team_ids = self.deduplicate(team_ids)

        json_list = await self.fetch_all("SELECT * FROM teams WHERE id = ANY($1)", team_ids)

        company_ids = tuple(json["company_id"] for json in json_list)

        companies, permissions = await gather(
            self.get_companies(*company_ids),
            self.get_permissions(*team_ids),
        )

        teams = {}

        for json in json_list:
            team_id = json["id"]

            company = companies[json["company_id"]]
            perms = permissions[team_id]

            team = json | {"company": company} | {"permissions": perms}
            teams[team_id] = team

        self.validate_ids(team_ids, teams.keys(), context="team")

        return teams

    async def get_companies(self, *company_ids: int) -> dict[int, Json]:
        if not company_ids:
            return {}

        company_ids = self.deduplicate(company_ids)

        json_list = await self.fetch_all(
            "SELECT * FROM companies WHERE id = ANY($1)", company_ids
        )

        companies = {json["id"]: json for json in json_list}

        self.validate_ids(company_ids, companies.keys(), context="company")

        return companies

    async def get_permissions(self, *team_ids: int) -> dict[int, list[Json]]:
        if not team_ids:
            return {}

        team_ids = self.deduplicate(team_ids)

        json_list = await self.fetch_all(
            "SELECT * FROM permissions WHERE team_id = ANY($1)", team_ids
        )

        permissions = {id_: [] for id_ in team_ids}

        for json in json_list:
            permissions[json["team_id"]].append(json)

        return permissions

    async def get_assignments(self, *ids: int, inverse: bool = False) -> dict[int, list[int]]:
        if not ids:
            return {}

        ids = self.deduplicate(ids)

        if inverse:
            key, val = "team_id", "user_id"
        else:
            key, val = "user_id", "team_id"

        json_list = await self.fetch_all(
            f"SELECT * FROM assignments WHERE {key} = ANY($1)", ids
        )

        assignments = {id_: [] for id_ in ids}

        for json in json_list:
            assignments[json[key]].append(json[val])

        return assignments

    async def get_quote(self, quote_id: int, /) -> Json | None:
        quote = await self.fetch_one("SELECT * FROM quotes WHERE id = $1", quote_id)

        if quote is None:
            return None

        owner_id = quote["owner_id"]

        json_list = await self.get_users(owner_id)
        owner = json_list[owner_id]

        return quote | {"owner": owner}

    async def get_quotes(self, *quote_ids: int) -> dict[int, Json]:
        if not quote_ids:
            return {}

        quote_ids = self.deduplicate(quote_ids)

        json_list = await self.fetch_all("SELECT * FROM quotes WHERE id = ANY($1)", quote_ids)

        owner_ids = (json["owner_id"] for json in json_list)

        owners = await self.get_users(*owner_ids)

        quotes = {}

        for json in json_list:
            quote_id = json["id"]
            owner = owners[json["owner_id"]]
            quote = json | {"owner": owner}
            quotes[quote_id] = quote

        self.validate_ids(quote_ids, quotes.keys(), context="quote")

        return quotes
