from __future__ import annotations

from typing import TYPE_CHECKING

from .bases_new import IntIdentifiable
from .codecs import ContainerCodec, PrimitiveCodec, SerialisableCodec
from .permissions import Permission, PermissionScope
from .team import Team

if TYPE_CHECKING:
    from .company import Company
    from .permissions import PermissionType

__all__ = ("User",)


class User(IntIdentifiable):
    codecs = {
        "username": PrimitiveCodec(str),
        "hashed_password": PrimitiveCodec(str, optional=True),
        "display_name": PrimitiveCodec(str, optional=True),
        "email": PrimitiveCodec(str, optional=True),
        "autopilot": PrimitiveCodec(bool),
        "admin": PrimitiveCodec(bool),
        "teams": ContainerCodec(frozenset, SerialisableCodec(Team)),
    }

    username: str
    hashed_password: str | None
    display_name: str | None
    email: str | None
    autopilot: bool
    admin: bool
    teams: frozenset[Team]

    def __str__(self):
        return self.display_name or self.username

    @property
    def companies(self) -> frozenset[Company]:
        return frozenset(team.company for team in self.teams)

    def highest_team_in(self, company: Company, /) -> Team | None:
        return max((team for team in self.teams if team.company == company), default=None)

    def has_permission_from(self, permission_type: PermissionType, other: User, /) -> bool:
        if self.admin or self == other:
            return True

        shared_companies = self.companies.intersection(other.companies)

        universal_perm = Permission.new(permission_type, PermissionScope.universal)
        company_perm = Permission.new(permission_type, PermissionScope.company)
        safe_perm = Permission.new(permission_type, PermissionScope.safe)

        # fmt: off
        if any(
            team.has_permission(universal_perm)
            for team in self.teams
        ):
            return True
        # fmt: on

        elif not shared_companies:
            return False

        elif any(
            team.company in shared_companies and team.has_permission(company_perm)
            for team in self.teams
        ):
            return True

        elif any(
            team.company in shared_companies
            and team >= other.highest_team_in(team.company)
            and team.has_permission(safe_perm)
            for team in self.teams
        ):
            return True

        else:
            return False
