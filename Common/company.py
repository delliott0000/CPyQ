from __future__ import annotations

from typing import TYPE_CHECKING

from .bases import ComparesIDABC, ComparesIDMixin

if TYPE_CHECKING:
    from typing import Any

    from asyncpg import Record

    Json = dict[str, Any]

__all__ = ("Company",)


class Company(ComparesIDMixin, ComparesIDABC):
    __slots__ = ("_id", "_name")

    def __init__(self, company_record: Record | Json, /):
        self._id = company_record["id"]
        self._name = company_record["name"]

    def __str__(self):
        return self._name

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    def to_json(self) -> Json:
        return {
            "id": self._id,
            "name": self._name,
        }
