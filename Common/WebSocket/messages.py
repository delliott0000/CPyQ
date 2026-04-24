from __future__ import annotations

from abc import ABC
from json import JSONDecodeError
from typing import TYPE_CHECKING
from uuid import uuid4

from aiohttp import WSMsgType

from ..bases import ComparesIDABC, ComparesIDMixin, JSONSerialisableABC
from ..utils import decode_datetime, encode_datetime, protocol_error, validate
from .enums import CustomWSCloseCode, CustomWSMessageType, WSEventStatus
from .payloads import parse_received_payload

if TYPE_CHECKING:
    from datetime import datetime
    from typing import Any, Self

    from aiohttp import WSMessage

    from .payloads import Payload

    Json = dict[str, Any]

__all__ = ("CustomWSMessage", "WSEvent", "WSAck", "make_id", "parse_received_message")


class CustomWSMessage(ComparesIDMixin, ComparesIDABC, JSONSerialisableABC, ABC):
    __slots__ = ("_type", "_id", "_sent_at")

    def __init__(self, json: Json, /, *, with_sent_at: bool):
        # Assume type already validated
        self._type = json["type"]
        self._id = json["id"]

        if with_sent_at:
            self._sent_at = decode_datetime(json["sent_at"])
        else:
            self._sent_at = None

        validate(str, self._id)

    @property
    def id(self) -> str:
        return self._id

    @property
    def sent_at(self) -> datetime | None:
        return self._sent_at

    @property
    def has_sent_at(self) -> bool:
        return self._sent_at is not None

    def with_sent_at(self, sent_at: datetime, /) -> Self:
        cls = type(self)
        json = self.json()
        json["sent_at"] = encode_datetime(sent_at)
        return cls(json, with_sent_at=True)

    def json(self) -> Json:
        json = {
            "type": self._type,
            "id": self._id,
        }

        if self.has_sent_at:
            json["sent_at"] = encode_datetime(self._sent_at)

        return json


class WSEvent(CustomWSMessage):
    __slots__ = ("_status", "_reason", "_payload")

    def __init__(self, json: Json, /, *, with_sent_at: bool):
        super().__init__(json, with_sent_at=with_sent_at)
        self._status = WSEventStatus(json["status"])
        self._reason = json.get("reason")
        self._payload = parse_received_payload(json["payload"])

        validate(str, self._reason, optional=True)

    @classmethod
    def from_payload(
        cls,
        payload: Payload,
        /,
        *,
        status: WSEventStatus = WSEventStatus.Normal,
        reason: str | None = None,
    ) -> Self:
        json = {
            "type": CustomWSMessageType.Event,
            "id": make_id(),
            "status": status,
            "reason": reason,
            "payload": payload.json(),
        }
        return cls(json, with_sent_at=False)

    @property
    def status(self) -> WSEventStatus:
        return self._status

    @property
    def is_fatal(self) -> bool:
        return self._status == WSEventStatus.Fatal

    @property
    def reason(self) -> str | None:
        return self._reason

    @property
    def payload(self) -> Payload:
        return self._payload

    def json(self) -> Json:
        return super().json() | {
            "status": self._status,
            "reason": self._reason,
            "payload": self._payload.json(),
        }


class WSAck(CustomWSMessage):
    __slots__ = ()

    @classmethod
    def from_event(cls, event: WSEvent, /) -> Self:
        json = {
            "type": CustomWSMessageType.Ack,
            "id": event.id,
        }
        return cls(json, with_sent_at=False)


_MAPPING = {
    CustomWSMessageType.Event: WSEvent,
    CustomWSMessageType.Ack: WSAck,
}


def make_id() -> str:
    return str(uuid4())


def parse_received_message(message: WSMessage, /) -> CustomWSMessage:
    if message.type != WSMsgType.TEXT:
        protocol_error(CustomWSCloseCode.InvalidFrameType)

    try:
        json = message.json()
        type_ = CustomWSMessageType(json["type"])
        cls = _MAPPING[type_]
        return cls(json, with_sent_at=True)

    except JSONDecodeError:
        protocol_error(CustomWSCloseCode.InvalidJSON)
    except KeyError:
        protocol_error(CustomWSCloseCode.MissingField)
    except TypeError:
        protocol_error(CustomWSCloseCode.InvalidType)
    except ValueError:
        protocol_error(CustomWSCloseCode.InvalidValue)
