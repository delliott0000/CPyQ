from __future__ import annotations

from typing import TYPE_CHECKING

from .payload import EMPTY_PAYLOAD

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, TypeVar

    from .enums import PayloadKind
    from .payload import Payload

    Json = dict[str, Any]
    PayloadT = TypeVar("PayloadT", bound=Payload)

__all__ = (
    "register_payload_kind",
    "payload_kind_to_cls",
    "payload_cls_to_kind",
    "parse_received_payload",
    "build_payload",
)


_PAYLOAD_MAP: dict[PayloadKind, type[Payload]] = {}
_PAYLOAD_RMAP: dict[type[Payload], PayloadKind] = {}


def register_payload_kind(kind: PayloadKind, /) -> Callable[[type[PayloadT]], type[PayloadT]]:

    def wrapper(cls: type[PayloadT], /) -> type[PayloadT]:
        _PAYLOAD_MAP[kind] = cls
        _PAYLOAD_RMAP[cls] = kind

        return cls

    return wrapper


def payload_kind_to_cls(kind: PayloadKind, /) -> type[Payload]:
    return _PAYLOAD_MAP[kind]


def payload_cls_to_kind(cls: type[Payload], /) -> PayloadKind:
    return _PAYLOAD_RMAP[cls]


def parse_received_payload(json: Json, /) -> Payload:
    if json == {}:
        return EMPTY_PAYLOAD

    else:
        kind = PayloadKind(json["kind"])
        cls = payload_kind_to_cls(kind)
        return cls(json)


def build_payload(cls: type[PayloadT], json: Json, /) -> PayloadT:
    if "kind" in json:
        raise ValueError('The supplied JSON contains a "kind" field.')

    kind = payload_cls_to_kind(cls)
    real_json = {**json, "kind": kind.value}
    return cls(real_json)
