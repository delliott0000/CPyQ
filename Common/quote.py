from __future__ import annotations

from typing import TYPE_CHECKING

from .bases import ComparesIDFormattedABC, ComparesIDFormattedMixin

if TYPE_CHECKING:
    from typing import Any

    from asyncpg import Record

    from .resource import ResourceJSONVersion
    from .user import User

__all__ = ("Quote",)


class Quote(ComparesIDFormattedMixin, ComparesIDFormattedABC):
    __slots__ = ("_id", "_owner")

    def __init__(self, quote_record: Record | dict, owner: User, /):
        self._id = quote_record["id"]
        self._owner = owner

    @property
    def id(self) -> int:
        return self._id

    @property
    def formatted_id(self) -> str: ...

    @property
    def owner(self) -> User:
        return self._owner

    def to_json(self, *, version: ResourceJSONVersion) -> dict[str, Any]: ...
