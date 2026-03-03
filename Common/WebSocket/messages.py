from __future__ import annotations

from json import JSONDecodeError
from typing import TYPE_CHECKING

from aiohttp import WSMsgType

from ..utils import decode_datetime, protocol_error
from .enums import CustomWSCloseCode, CustomWSMessageType, WSEventStatus

if TYPE_CHECKING:
    from datetime import datetime
    from typing import Any

    from aiohttp import WSMessage

    Json = dict[str, Any]

__all__ = ("CustomWSMessage", "WSEvent", "WSAck", "custom_message_factory")


class CustomWSMessage:
    def __init__(self, json: Json, /):
        self._id = json["id"]
        self._sent_at = decode_datetime(json["sent_at"])

        if not isinstance(self._id, str):
            raise TypeError("UUID must be a string.")

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
        self._payload = json["payload"]

        if not (isinstance(self._reason, str) or self._reason is None):
            raise TypeError("Reason must be a string or None.")
        elif not isinstance(self._payload, dict):
            raise TypeError("Payload must be a dict.")

    @property
    def status(self) -> WSEventStatus:
        return self._status

    @property
    def reason(self) -> str | None:
        return self._reason

    @property
    def payload(self) -> Json:
        return self._payload


class WSAck(CustomWSMessage):
    pass


def custom_message_factory(message: WSMessage, /) -> WSEvent | WSAck:
    if message.type != WSMsgType.TEXT:
        protocol_error(CustomWSCloseCode.InvalidFrameType)

    try:
        json = message.json()
        type_ = CustomWSMessageType(json["type"])
        mapping = {CustomWSMessageType.Event: WSEvent, CustomWSMessageType.Ack: WSAck}
        cls = mapping[type_]
        return cls(json)

    except JSONDecodeError:
        protocol_error(CustomWSCloseCode.InvalidJSON)
    except KeyError:
        protocol_error(CustomWSCloseCode.MissingField)
    except TypeError:
        protocol_error(CustomWSCloseCode.InvalidType)
    except ValueError:
        protocol_error(CustomWSCloseCode.InvalidValue)
