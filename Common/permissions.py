from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from .bases import JSONSerialisableABC

if TYPE_CHECKING:
    from typing import Any

    Json = dict[str, Any]

__all__ = ("PermissionType", "PermissionScope", "Permission")


# fmt: off
class PermissionType(Enum):
    create   = "create"
    preview  = "preview"
    view     = "view"
    acquire  = "acquire"
    update   = "update"
    generate = "generate"
    delete   = "delete"
    reassign = "reassign"


class PermissionScope(Enum):
    safe      = "safe"
    company   = "company"
    universal = "universal"
    null      = None

    __rank__ = {safe: 0, company: 1, universal: 2}

    def __check_null__(self, other):
        if not isinstance(other, PermissionScope):
            return NotImplemented
        return self.value is None or other.value is None

    def __lt__(self, other):
        return self.__check_null__(other) or self.__rank__[self.value] < self.__rank__[other.value]  # noqa

    def __gt__(self, other):
        return self.__check_null__(other) or self.__rank__[self.value] > self.__rank__[other.value]  # noqa


@dataclass(kw_only=True, frozen=True, slots=True)
class Permission(JSONSerialisableABC):
    type:  PermissionType
    scope: PermissionScope

    def json(self) -> Json:
        return {
            "type": self.type.value,
            "scope": self.scope.value,
        }
# fmt: on
