from __future__ import annotations

from enum import IntEnum, StrEnum
from json import JSONDecodeError
from typing import TYPE_CHECKING

from aiohttp import ClientWebSocketResponse, WSCloseCode, WSMsgType
from aiohttp.web import WebSocketResponse

from .errors import InvalidFrameType, RatelimitExceeded
from .utils import check_ratelimit, decode_datetime

if TYPE_CHECKING:
    from datetime import datetime
    from typing import Any

    Json = dict[str, Any]

__all__ = (
    "CustomWSMessageType",
    "WSEventStatus",
    "CustomWSCloseCode",
    "CustomWSMessage",
    "WSEvent",
    "WSAck",
    "custom_ws_message_factory",
    "WSResponseMixin",
    "CustomWSResponse",
    "CustomClientWSResponse",
)


# fmt: off
class CustomWSMessageType(StrEnum):
    Event = "event"
    Ack   = "ack"


class WSEventStatus(StrEnum):
    Ok    = "ok"
    Error = "error"
    Fatal = "fatal"


class CustomWSCloseCode(IntEnum):
    TokenExpired       = 4000
    InvalidFrameType   = 4001
    InvalidJSON        = 4002
    MissingField       = 4003
    InvalidType        = 4004
    InvalidValue       = 4005
# fmt: on


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


def custom_ws_message_factory(json: Json, /) -> WSEvent | WSAck:
    message_type = CustomWSMessageType(json["type"])
    mapping = {CustomWSMessageType.Event: WSEvent, CustomWSMessageType.Ack: WSAck}
    cls = mapping[message_type]
    return cls(json)


class WSResponseMixin:
    def __init__(
        self,
        *,
        ratelimited: bool = False,
        limit: int | None = None,
        interval: float | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)

        if ratelimited and (limit is None or interval is None):
            raise TypeError("Limit and interval must both be specified.")

        self.__ratelimited = ratelimited
        self.__limit = limit
        self.__interval = interval
        self.__hits = []

    async def __anext__(self) -> WSEvent:
        try:
            while True:
                message = await super().__anext__()  # noqa

                if self.__ratelimited:
                    self.__hits = check_ratelimit(
                        self.__hits, limit=self.__limit, interval=self.__interval
                    )

                if message.type != WSMsgType.TEXT:
                    raise InvalidFrameType(message)

                custom_message = custom_ws_message_factory(message.json())

                if isinstance(custom_message, WSAck):
                    ...

                    continue

                else:
                    ...

                    return custom_message

        except Exception as error:
            mapping = {
                RatelimitExceeded: WSCloseCode.POLICY_VIOLATION,
                InvalidFrameType: CustomWSCloseCode.InvalidFrameType,
                JSONDecodeError: CustomWSCloseCode.InvalidJSON,
                KeyError: CustomWSCloseCode.MissingField,
                TypeError: CustomWSCloseCode.InvalidType,
                ValueError: CustomWSCloseCode.InvalidValue,
            }
            cls = type(error)

            if cls in mapping:
                await self.close(code=mapping[cls])  # noqa
                raise StopAsyncIteration

            else:
                raise error


class CustomWSResponse(WSResponseMixin, WebSocketResponse):
    pass


class CustomClientWSResponse(WSResponseMixin, ClientWebSocketResponse):
    pass
