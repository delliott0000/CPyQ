from __future__ import annotations

from typing import TYPE_CHECKING

from .bases import ComparesIDABC, ComparesIDMixin, JSONSerialisableABC
from .permissions import Permission, PermissionScope

if TYPE_CHECKING:
    from typing import Any

    from .company import Company
    from .permissions import PermissionType
    from .team import Team

    Json = dict[str, Any]

__all__ = ("User",)


class User(ComparesIDMixin, ComparesIDABC, JSONSerialisableABC):
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

    def __init__(self, json: Json, teams: frozenset[Team], /):
        self._id = json["id"]
        self._username = json["username"]
        self._hashed_password = json.get("hashed_password")
        self._display_name = json["display_name"]
        self._email = json["email"]
        self._autopilot = json["autopilot"]
        self._admin = json["admin"]
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

    def has_permission_from(self, permission_type: PermissionType, other: User, /) -> bool:
        if self._admin or self == other:
            return True

        shared_companies = self.companies.intersection(other.companies)

        if any(
            team.has_permission(Permission.new(permission_type, PermissionScope.universal))
            for team in self._teams
        ):
            return True

        elif not shared_companies:
            return False

        elif any(
            team.company in shared_companies
            and team.has_permission(Permission.new(permission_type, PermissionScope.company))
            for team in self._teams
        ):
            return True

        elif any(
            team.company in shared_companies
            and team >= other.highest_team_in(team.company)
            and team.has_permission(Permission.new(permission_type, PermissionScope.safe))
            for team in self._teams
        ):
            return True

        else:
            return False

    def json(self) -> Json:
        return {
            "id": self._id,
            "username": self._username,
            "display_name": self._display_name,
            "email": self._email,
            "autopilot": self._autopilot,
            "admin": self._admin,
            "teams": list(team.json() for team in self._teams),
        }
