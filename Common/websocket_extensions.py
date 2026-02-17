from __future__ import annotations

from enum import IntEnum, StrEnum
from json import JSONDecodeError
from typing import TYPE_CHECKING

from aiohttp import ClientWebSocketResponse, WSCloseCode, WSMsgType
from aiohttp.web import WebSocketResponse

from .errors import RatelimitException, WSException
from .utils import check_ratelimit, decode_datetime

if TYPE_CHECKING:
    from asyncio import Task
    from datetime import datetime
    from typing import Any

    from aiohttp import WSMessage

    Json = dict[str, Any]

__all__ = (
    "CustomWSMessageType",
    "WSEventStatus",
    "CustomWSCloseCode",
    "CustomWSMessage",
    "WSEvent",
    "WSAck",
    "protocol_error",
    "custom_message_factory",
    "WSResponseMixin",
    "CustomWSResponse",
    "CustomClientWSResponse",
)


# fmt: off
class CustomWSMessageType(StrEnum):
    Event = "event"
    Ack   = "ack"


class WSEventStatus(StrEnum):
    Normal = "normal"
    Error  = "error"
    Fatal  = "fatal"


class CustomWSCloseCode(IntEnum):
    TokenExpired       = 4000
    InvalidFrameType   = 4001
    InvalidJSON        = 4002
    MissingField       = 4003
    InvalidType        = 4004
    InvalidValue       = 4005
    DuplicateEventID   = 4006
    AckTimeout         = 4007
    UnknownEvent       = 4008
    FatalEvent         = 4009
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


def protocol_error(code: IntEnum, /) -> None:
    raise WSException(code=code)


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

        self.ratelimited = ratelimited
        self.limit = limit
        self.interval = interval
        self.__hits = []

        self.__sent_unacked: dict[str, Task] = {}
        self.__recv_unacked: set[str] = set()
        self.__tasks: set[Task] = set()

    async def __anext__(self) -> WSEvent:
        try:
            while True:
                message = await super().__anext__()  # noqa

                if self.ratelimited:
                    check_ratelimit(self.__hits, limit=self.limit, interval=self.interval)

                custom_message = custom_message_factory(message)

                if isinstance(custom_message, WSEvent):
                    self.__event__(custom_message)
                    return custom_message

                else:
                    self.__ack__(custom_message)
                    # continue

        except RatelimitException:
            await self.close(code=WSCloseCode.POLICY_VIOLATION)
        except WSException as error:
            await self.close(code=error.code)

        raise StopAsyncIteration

    def __event__(self, event: WSEvent, /) -> None: ...

    def __ack__(self, ack: WSAck, /) -> None: ...

    async def close(self, **kwargs: Any) -> bool:
        result = await super().close(**kwargs)  # noqa

        if result is True:
            ...

        return result


class CustomWSResponse(WSResponseMixin, WebSocketResponse):
    pass


class CustomClientWSResponse(WSResponseMixin, ClientWebSocketResponse):
    pass
