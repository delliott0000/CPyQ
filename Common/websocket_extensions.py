from __future__ import annotations

from enum import IntEnum, StrEnum
from json import JSONDecodeError
from typing import TYPE_CHECKING

from aiohttp import ClientWebSocketResponse, WSCloseCode, WSMsgType
from aiohttp.web import WebSocketResponse

from .bases import ComparesIDABC, ComparesIDMixin
from .utils import check_ratelimit, decode_datetime

if TYPE_CHECKING:
    from datetime import datetime
    from typing import Any

    Json = dict[str, Any]

__all__ = (
    "custom_ws_message_factory",
    "CustomWSMessageType",
    "WSEventStatus",
    "CustomWSCloseCode",
    "CustomWSMessage",
    "WSEvent",
    "WSAck",
    "WSResponseMixin",
    "CustomWSResponse",
    "CustomClientWSResponse",
)


def custom_ws_message_factory(json: Json, /) -> CustomWSMessage:
    message_type = CustomWSMessageType(json["type"])
    mapping = {CustomWSMessageType.Event: WSEvent, CustomWSMessageType.Ack: WSAck}
    cls = mapping[message_type]
    return cls(json)


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


class CustomWSMessage(ComparesIDMixin, ComparesIDABC):
    def __init__(self, json: Json, /):
        self._id = json["id"]
        self._sent_at = decode_datetime(json["sent_at"])

    @property
    def id(self) -> Any:
        return self._id

    @property
    def sent_at(self) -> datetime:
        return self._sent_at


class WSEvent(CustomWSMessage): ...


class WSAck(CustomWSMessage):
    pass


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

    async def __anext__(self) -> CustomWSMessage:
        message = await super().__anext__()  # noqa

        if self.__ratelimited:
            try:
                self.__hits = check_ratelimit(
                    self.__hits, limit=self.__limit, interval=self.__interval
                )
            except RuntimeError:
                await self.__close_and_break__(code=WSCloseCode.POLICY_VIOLATION)

        if message.type != WSMsgType.TEXT:
            await self.__close_and_break__(code=CustomWSCloseCode.InvalidFrameType)

        try:
            custom_message = custom_ws_message_factory(message.json())
        except JSONDecodeError:
            await self.__close_and_break__(code=CustomWSCloseCode.InvalidJSON)
        except KeyError:
            await self.__close_and_break__(code=CustomWSCloseCode.MissingField)
        except TypeError:
            await self.__close_and_break__(code=CustomWSCloseCode.InvalidType)
        except ValueError:
            await self.__close_and_break__(code=CustomWSCloseCode.InvalidValue)

        return custom_message  # noqa

    async def __close_and_break__(self, **kwargs: Any) -> None:
        await self.close(**kwargs)  # noqa
        raise StopAsyncIteration


class CustomWSResponse(WSResponseMixin, WebSocketResponse):
    pass


class CustomClientWSResponse(WSResponseMixin, ClientWebSocketResponse):
    pass
