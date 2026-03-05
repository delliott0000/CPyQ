from __future__ import annotations

from typing import TYPE_CHECKING

from .bases import ComparesIDABC, ComparesIDMixin

if TYPE_CHECKING:
    from typing import Any

    from asyncpg import Record

    from .company import Company
    from .permissions import Permission

    Json = dict[str, Any]

__all__ = ("Team",)


class Team(ComparesIDMixin, ComparesIDABC):
    __slots__ = ("_id", "_name", "_hierarchy_index", "_company", "_permissions")

    def __init__(
        self,
        team_record: Record | Json,
        company: Company,
        permissions: frozenset[Permission],
        /,
    ):
        self._id = team_record["id"]
        self._name = team_record["name"]
        self._hierarchy_index = team_record["hierarchy_index"]
        self._company = company
        self._permissions = permissions

    def __str__(self):
        return self._name

    def __lt__(self, other):
        return self.__comparison_check__(other) or self.hierarchy_index < other.hierarchy_index

    def __gt__(self, other):
        return self.__comparison_check__(other) or self.hierarchy_index > other.hierarchy_index

    def __le__(self, other):
        return self.__comparison_check__(other) or self.hierarchy_index <= other.hierarchy_index

    def __ge__(self, other):
        return self.__comparison_check__(other) or self.hierarchy_index >= other.hierarchy_index

    def __comparison_check__(self, other):
        if not isinstance(other, Team):
            return NotImplemented
        elif self.company != other.company:
            raise RuntimeError("Cannot compare two teams from different companies.")
        return False

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def hierarchy_index(self) -> int:
        return self._hierarchy_index

    @property
    def company(self) -> Company:
        return self._company

    @property
    def permissions(self) -> frozenset[Permission]:
        return self._permissions

    def has_permission(self, permission: Permission, /) -> bool:
        # fmt: off
        return (
            permission in self._permissions
            or
            any(
                perm.type == permission.type
                and
                perm.scope > permission.scope
                for perm in self._permissions
            )
        )
        # fmt: on

    def to_json(self) -> Json:
        return {
            "id": self._id,
            "name": self._name,
            "hierarchy_index": self._hierarchy_index,
            "company": self._company.to_json(),
            "permissions": list(permission.to_json() for permission in self._permissions),
        }
