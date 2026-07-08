from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import TypeVar

    from .enums import PayloadKind
    from .payload import Payload

    PayloadT = TypeVar("PayloadT", bound=Payload)

__all__ = (
    "register_kind",
    "payload_kind_to_cls",
    "payload_cls_to_kind",
)


_PAYLOAD_MAP: dict[PayloadKind, type[Payload]] = {}
_PAYLOAD_RMAP: dict[type[Payload], PayloadKind] = {}


def register_kind(kind: PayloadKind, /) -> Callable[[type[PayloadT]], type[PayloadT]]:

    def wrapper(cls: type[PayloadT], /) -> type[PayloadT]:
        _PAYLOAD_MAP[kind] = cls
        _PAYLOAD_RMAP[cls] = kind

        return cls

    return wrapper


def payload_kind_to_cls(kind: PayloadKind, /) -> type[Payload]:
    return _PAYLOAD_MAP[kind]


def payload_cls_to_kind(cls: type[Payload], /) -> PayloadKind:
    return _PAYLOAD_RMAP[cls]
