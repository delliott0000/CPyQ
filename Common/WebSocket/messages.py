from __future__ import annotations

from json import JSONDecodeError
from typing import TYPE_CHECKING

from aiohttp import WSMsgType

from ..utils import decode_datetime, protocol_error, validate
from .enums import CustomWSCloseCode, CustomWSMessageType, WSEventStatus
from .payloads import payload_factory

if TYPE_CHECKING:
    from datetime import datetime
    from typing import Any

    from aiohttp import WSMessage

    from .payloads import Payload

    Json = dict[str, Any]

__all__ = ("CustomWSMessage", "WSEvent", "WSAck", "custom_message_factory")


class CustomWSMessage:
    def __init__(self, json: Json, /):
        self._id = json["id"]
        self._sent_at = decode_datetime(json["sent_at"])

        validate(str, self._id)

    @property
    def id(self) -> str:
        return self._id

    @property
    def sent_at(self) -> datetime:
        return self._sent_at


class WSEvent(CustomWSMessage):
    def __init__(self, json: Json, /):
        super().__init__(json)
        self._status = WSEventStatus(json["status"])
        self._reason = json.get("reason")
        self._payload = payload_factory(json["payload"])

        validate(str, self._reason, optional=True)

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


class WSAck(CustomWSMessage):
    pass


_MAPPING = {
    CustomWSMessageType.Event: WSEvent,
    CustomWSMessageType.Ack: WSAck,
}


def custom_message_factory(message: WSMessage, /) -> CustomWSMessage:
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
