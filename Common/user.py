from __future__ import annotations

from typing import TYPE_CHECKING

from .bases import ComparesIDABC, ComparesIDMixin
from .permissions import Permission, PermissionScope

if TYPE_CHECKING:
    from typing import Any

    from asyncpg import Record

    from .company import Company
    from .permissions import PermissionType
    from .resource import Resource
    from .team import Team

__all__ = ("User",)


class User(ComparesIDMixin, ComparesIDABC):
    __slots__ = (
        "_id",
        "_username",
        "_hashed_password",
        "_display_name",
        "_email",
        "_autopilot",
        "_admin",
        "_teams",
    )

    def __init__(self, user_record: Record | dict, teams: frozenset[Team], /):
        self._id = user_record["id"]
        self._username = user_record["username"]
        self._hashed_password = user_record.get("hashed_password")
        self._display_name = user_record["display_name"]
        self._email = user_record["email"]
        self._autopilot = user_record["autopilot"]
        self._admin = user_record["admin"]
        self._teams = teams

    def __str__(self):
        return self._display_name or self._username

    @property
    def id(self) -> int:
        return self._id

    @property
    def username(self) -> str:
        return self._username

    @property
    def hashed_password(self) -> str | None:
        return self._hashed_password

    @property
    def display_name(self) -> str | None:
        return self._display_name

    @property
    def email(self) -> str | None:
        return self._email

    @property
    def autopilot(self) -> bool:
        return self._autopilot

    @property
    def admin(self) -> bool:
        return self._admin

    @property
    def teams(self) -> frozenset[Team]:
        return self._teams

    @property
    def companies(self) -> frozenset[Company]:
        return frozenset(team.company for team in self._teams)

    def highest_team_in(self, company: Company, /) -> Team | None:
        return max((team for team in self._teams if team.company == company), default=None)

    def has_permission_for(
        self, permission_type: PermissionType, resource: Resource, /
    ) -> bool:
        if self._admin:
            return True

        owner = resource.owner
        shared_companies = self.companies.intersection(owner.companies)

        if any(
            team.has_permission(
                Permission(type=permission_type, scope=PermissionScope.universal)
            )
            for team in self._teams
        ):
            return True

        elif not shared_companies:
            return False

        elif any(
            team.company in shared_companies
            and team.has_permission(
                Permission(type=permission_type, scope=PermissionScope.company)
            )
            for team in self._teams
        ):
            return True

        elif any(
            team.company in shared_companies
            and team >= owner.highest_team_in(team.company)
            and team.has_permission(
                Permission(type=permission_type, scope=PermissionScope.safe)
            )
            for team in self._teams
        ):
            return True

        else:
            return False

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self._id,
            "username": self._username,
            "display_name": self._display_name,
            "email": self._email,
            "autopilot": self._autopilot,
            "admin": self._admin,
            "teams": list(team.to_json() for team in self._teams),
        }
