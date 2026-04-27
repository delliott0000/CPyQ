from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ..bases import JSONSerialisableABC
from ..codecs import float_codec
from ..utils import validate
from .enums import PayloadKind, WSPeerType

if TYPE_CHECKING:
    from typing import Any, ClassVar

    from ..codecs import Codec
    from .response import WSProxy

    Json = dict[str, Any]

__all__ = (
    "Payload",
    "EmptyPayload",
    "Handshake",
    "UserHandshake",
    "AutopilotHandshake",
    "EMPTY_PAYLOAD",
    "payload_kind_to_cls",
    "payload_cls_to_kind",
    "peer_type_to_handshake_cls",
    "parse_received_payload",
    "build_payload",
)


class Payload(JSONSerialisableABC, ABC):
    CODECS: ClassVar[dict[str, Codec] | None] = None

    def __init__(self, json: Json, /):
        if type(self) is Payload:
            raise NotImplementedError(
                "Payload is an abstract base class and must not be instantiated directly."
            )
        elif self.CODECS is None:
            raise RuntimeError("Payload subclasses must each define their own codecs.")

        # Already validated by the factory
        self._kind = json["kind"]

        for key, codec in self.CODECS.items():
            setattr(self, key, codec.decode(json[key]))

    @abstractmethod
    def valid_context(self, *, receiver: WSProxy) -> bool:
        pass

    def json(self) -> Json:
        return {"kind": self._kind} | {
            key: codec.encode(getattr(self, key)) for key, codec in self.CODECS.items()
        }


class EmptyPayload(Payload):
    def __init__(self, _: Json):  # noqa
        pass

    def valid_context(self, *, receiver: WSProxy) -> bool: ...

    def json(self) -> Json:
        return {}


class Handshake(Payload, ABC):
    CODECS = {
        "ack_timeout": float_codec,
    }

    ack_timeout: float


class UserHandshake(Handshake):
    # TODO: Add more fields as/when needed
    CODECS = Handshake.CODECS | {}

    ...

    def valid_context(self, *, receiver: WSProxy) -> bool: ...


class AutopilotHandshake(Handshake):
    # TODO: Add more fields as/when needed
    CODECS = Handshake.CODECS | {}

    ...

    def valid_context(self, *, receiver: WSProxy) -> bool: ...


EMPTY_PAYLOAD = EmptyPayload({})


_PAYLOAD_MAP: dict[PayloadKind, type[Payload]] = {
    PayloadKind.UserHandshake: UserHandshake,
    PayloadKind.AutopilotHandshake: AutopilotHandshake,
}


def payload_kind_to_cls(kind: PayloadKind, /) -> type[Payload]:
    return _PAYLOAD_MAP[kind]


_PAYLOAD_RMAP: dict[type[Payload], PayloadKind] = {v: k for k, v in _PAYLOAD_MAP.items()}


def payload_cls_to_kind(cls: type[Payload], /) -> PayloadKind:
    return _PAYLOAD_RMAP[cls]


_HANDSHAKE_MAP: dict[WSPeerType, type[Handshake]] = {
    WSPeerType.User: UserHandshake,
    WSPeerType.Autopilot: AutopilotHandshake,
}


def peer_type_to_handshake_cls(peer_type: WSPeerType, /) -> type[Handshake]:
    return _HANDSHAKE_MAP[peer_type]


def parse_received_payload(json: Json, /) -> Payload:
    validate(dict, json)

    if not json:
        return EMPTY_PAYLOAD

    else:
        kind = PayloadKind(json["kind"])
        cls = payload_kind_to_cls(kind)
        return cls(json)


if TYPE_CHECKING:
    from typing import TypeVar

    PayloadT = TypeVar("PayloadT", bound=Payload)


def build_payload(cls: type[PayloadT], json: Json, /) -> PayloadT:
    if "kind" in json:
        raise ValueError('The supplied JSON contains a "kind" field.')

    kind = payload_cls_to_kind(cls)
    real_json = {**json, "kind": kind}
    return cls(real_json)
