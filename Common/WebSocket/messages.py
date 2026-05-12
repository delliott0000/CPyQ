from __future__ import annotations

from json import JSONDecodeError
from typing import TYPE_CHECKING
from uuid import uuid4

from aiohttp import WSMsgType

from ..bases_new import StrIdentifiable
from ..codecs import DatetimeCodec, EnumCodec, PrimitiveCodec, SerialisableCodec
from ..utils import encode_datetime, protocol_error
from .enums import CustomWSCloseCode, CustomWSMessageType, WSEventStatus
from .payloads import parse_received_payload

if TYPE_CHECKING:
    from datetime import datetime
    from typing import Self

    from aiohttp import WSMessage

    from .payloads import Payload

__all__ = ("CustomWSMessage", "WSEvent", "WSAck", "make_id", "parse_received_message")


class CustomWSMessage(StrIdentifiable):
    codecs = {
        "type": EnumCodec(CustomWSMessageType),
        "sent_at": DatetimeCodec(optional=True),
    }

    type: CustomWSMessageType
    sent_at: datetime | None

    def with_sent_at(self, sent_at: datetime, /) -> Self:
        cls = type(self)
        json = self.json()
        json["sent_at"] = encode_datetime(sent_at)
        return cls(json)


class WSEvent(CustomWSMessage):
    codecs = {
        "status": EnumCodec(WSEventStatus),
        "reason": PrimitiveCodec(str, optional=True),
        "payload": SerialisableCodec(parse_received_payload),
    }

    status: WSEventStatus
    reason: str | None
    payload: Payload

    @property
    def is_fatal(self) -> bool:
        return self.status == WSEventStatus.Fatal

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
            "type": CustomWSMessageType.Event.value,
            "id": make_id(),
            "sent_at": None,
            "status": status.value,
            "reason": reason,
            "payload": payload.json(),
        }
        return cls(json)


class WSAck(CustomWSMessage):
    @classmethod
    def from_event(cls, event: WSEvent, /) -> Self:
        json = {
            "type": CustomWSMessageType.Ack.value,
            "id": event.id,
            "sent_at": None,
        }
        return cls(json)


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
        return cls(json)

    except JSONDecodeError:
        protocol_error(CustomWSCloseCode.InvalidJSON)
    except KeyError:
        protocol_error(CustomWSCloseCode.MissingField)
    except TypeError:
        protocol_error(CustomWSCloseCode.InvalidType)
    except ValueError:
        protocol_error(CustomWSCloseCode.InvalidValue)
