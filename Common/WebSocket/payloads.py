from __future__ import annotations

from typing import TYPE_CHECKING

from ..bases import Serialisable
from ..codecs import EnumCodec, PrimitiveCodec, SerialisableCodec
from ..task import Task
from .enums import PayloadKind, WSPeerType

if TYPE_CHECKING:
    from typing import Any

    from .response import WSProxy

    Json = dict[str, Any]

__all__ = (
    "Payload",
    "EmptyPayload",
    "NonEmptyPayload",
    "Handshake",
    "UserHandshake",
    "AutopilotHandshake",
    "TaskAssigned",
    "TaskDone",
    "EMPTY_PAYLOAD",
    "payload_kind_to_cls",
    "payload_cls_to_kind",
    "peer_type_to_handshake_cls",
    "parse_received_payload",
    "build_payload",
)


class Payload(Serialisable):
    def valid_context(self, *, receiver: WSProxy) -> bool:
        raise NotImplementedError


class EmptyPayload(Payload):
    def valid_context(self, *, receiver: WSProxy) -> bool:
        return receiver.handshake_done


class NonEmptyPayload(Payload):
    codecs = {
        "kind": EnumCodec(PayloadKind),
    }

    kind: PayloadKind


class Handshake(NonEmptyPayload):
    codecs = {
        "ack_timeout": PrimitiveCodec(float),
    }

    ack_timeout: float

    def valid_context(self, *, receiver: WSProxy) -> bool:
        return (
            not receiver.server and not receiver.handshake_set and receiver.is_handshake(self)
        )


class UserHandshake(Handshake):
    codecs = {}


class AutopilotHandshake(Handshake):
    codecs = {}


class TaskAssigned(NonEmptyPayload):
    codecs = {
        "task": SerialisableCodec(Task),
    }

    task: Task

    def valid_context(self, *, receiver: WSProxy) -> bool:
        return (
            not receiver.server
            and receiver.handshake_done
            and receiver.peer_type == WSPeerType.Autopilot
        )


class TaskDone(NonEmptyPayload):
    codes = {
        "task_id": PrimitiveCodec(int),
    }

    task_id: int

    def valid_context(self, *, receiver: WSProxy) -> bool:
        return (
            receiver.server
            and receiver.handshake_done
            and receiver.peer_type == WSPeerType.Autopilot
        )


EMPTY_PAYLOAD = EmptyPayload({})


_PAYLOAD_MAP: dict[PayloadKind, type[Payload]] = {
    PayloadKind.UserHandshake: UserHandshake,
    PayloadKind.AutopilotHandshake: AutopilotHandshake,
    PayloadKind.TaskAssigned: TaskAssigned,
    PayloadKind.TaskDone: TaskDone,
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
    if json == {}:
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
