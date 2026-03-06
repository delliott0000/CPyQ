from __future__ import annotations

from typing import TYPE_CHECKING

from .bases import ComparesIDFormattedABC, ComparesIDFormattedMixin, JSONSerialisableABC
from .resource import ResourceJSONVersion

if TYPE_CHECKING:
    from typing import Any

    from asyncpg import Record

    from .user import User

    Json = dict[str, Any]

__all__ = ("Quote",)


class Quote(ComparesIDFormattedMixin, ComparesIDFormattedABC, JSONSerialisableABC):
    __slots__ = ("_id", "_owner")

    def __init__(self, quote_record: Record | Json, owner: User, /):
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

    def json(self, *, version: ResourceJSONVersion = ResourceJSONVersion.default) -> Json: ...
