from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from .bases import Serialisable
from .codecs import EnumCodec

if TYPE_CHECKING:
    from typing import Self

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
    # fmt: on

    __rank__ = {safe: 0, company: 1, universal: 2}

    def __check_null__(self, other):
        if not isinstance(other, PermissionScope):
            return NotImplemented
        return self.value is None or other.value is None

    def __lt__(self, other):
        return self.__check_null__(other) or self.__rank__[self.value] < self.__rank__[other.value]  # noqa

    def __gt__(self, other):
        return self.__check_null__(other) or self.__rank__[self.value] > self.__rank__[other.value]  # noqa


class Permission(Serialisable):
    codecs = {
        "type": EnumCodec(PermissionType),
        "scope": EnumCodec(PermissionScope),
    }

    type: PermissionType
    scope: PermissionScope

    @classmethod
    def new(cls, permission_type: PermissionType, permission_scope: PermissionScope, /) -> Self:
        return cls(
            {
                "type": permission_type.value,
                "scope": permission_scope.value,
            }
        )
