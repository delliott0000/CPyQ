from __future__ import annotations

from asyncio import CancelledError, create_task, get_running_loop
from enum import IntEnum, StrEnum
from json import JSONDecodeError
from logging import ERROR
from typing import TYPE_CHECKING

from aiohttp import ClientWebSocketResponse, WSCloseCode, WSMsgType
from aiohttp.web import WebSocketResponse

from .errors import RatelimitException, WSException
from .utils import check_ratelimit, decode_datetime, log

if TYPE_CHECKING:
    from asyncio import Future, Task
    from collections.abc import Coroutine
    from datetime import datetime
    from typing import Any

    from aiohttp import WSMessage

    Json = dict[str, Any]
    Coro = Coroutine[Any, Any, None]
    TN = Task[None]

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
    InternalError      = 4999
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

        self.__sent_unacked: dict[str, TN] = dict()
        self.__recv_unacked: set[str] = set()

        self.__submitted_tasks: set[TN] = set()

        self.__error_futr: Future[IntEnum] = get_running_loop().create_future()
        self.__error_task: TN = create_task(self.__wait_for_close__())

    async def __anext__(self) -> WSEvent:
        try:
            while True:
                message = await super().__anext__()  # noqa

                if self.ratelimited:
                    check_ratelimit(self.__hits, limit=self.limit, interval=self.interval)

                custom_message = custom_message_factory(message)

                if isinstance(custom_message, WSEvent):
                    self.__recv_event__(custom_message)
                    return custom_message

                else:
                    self.__recv_ack__(custom_message)
                    # continue

        except RatelimitException:
            await self.close(code=WSCloseCode.POLICY_VIOLATION)
        except WSException as error:
            await self.close(code=error.code)

        raise StopAsyncIteration

    def __recv_event__(self, event: WSEvent, /) -> None: ...

    def __recv_ack__(self, ack: WSAck, /) -> None: ...

    def __signal_close__(self, code: IntEnum, /) -> None: ...

    async def __wait_for_close__(self) -> None:
        code = await self.__error_futr
        await self.close(_cancel_all=False, code=code)

    async def __coro_wrapper__(self, coro: Coro, /) -> None:
        try:
            await coro
        except CancelledError:
            log(f"WebSocket task {coro} was cancelled.")
        except WSException as error:
            self.__signal_close__(error.code)
        except Exception as error:
            log(f"WebSocket task {coro} raised an exception.", ERROR, error=error)
            self.__signal_close__(CustomWSCloseCode.InternalError)

    def submit(self, coro: Coro, /) -> None: ...

    async def close(self, _cancel_all: bool = True, **kwargs: Any) -> bool:
        result = await super().close(**kwargs)  # noqa

        if result is True:
            ...

        return result


class CustomWSResponse(WSResponseMixin, WebSocketResponse):
    pass


class CustomClientWSResponse(WSResponseMixin, ClientWebSocketResponse):
    pass
