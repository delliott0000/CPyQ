from __future__ import annotations

from asyncio import CancelledError, Queue, create_task
from logging import DEBUG, ERROR
from typing import TYPE_CHECKING, Protocol

from aiohttp import WSCloseCode

from ..errors import RatelimitException, WSException
from ..utils import check_ratelimit, log, make_future
from .enums import CustomWSCloseCode
from .messages import WSAck, WSEvent, parse_received_message

if TYPE_CHECKING:
    from asyncio import Future, Task
    from collections.abc import AsyncIterator, Coroutine
    from typing import Any

    from aiohttp import WSMessage

    Json = dict[str, Any]
    CN = Coroutine[Any, Any, None]
    TN = Task[None]
    CloseCode = WSCloseCode | CustomWSCloseCode

__all__ = ("WSResponseType", "WSProxy")


class WSResponseType(Protocol):
    def __aiter__(self) -> AsyncIterator[WSMessage]: ...
    @property
    def close_code(self) -> int | None: ...
    async def send_json(self, json: Json, /) -> Any: ...
    async def close(self, *, code: CloseCode = ...) -> Any: ...


class WSProxy:
    __slots__ = (
        "__response",
        "__ratelimited",
        "__limit",
        "__interval",
        "__hits",
        "__sent_unacked",
        "__received_unacked",
        "__submitted_tasks",
        "__queue",
        "__close_future",
        "__close_task",
        "__reader_task",
        "__started",
        "__closed",
    )

    def __init__(
        self,
        response: WSResponseType,
        /,
        *,
        ratelimited: bool = False,
        limit: int | None = None,
        interval: float | None = None,
        start: bool = False,
    ):
        if ratelimited and (limit is None or interval is None):
            raise TypeError("Limit and interval must both be specified.")

        self.__response = response

        self.__ratelimited = ratelimited
        self.__limit = limit
        self.__interval = interval
        self.__hits: list[float] = []

        self.__sent_unacked: dict[WSEvent, TN] = dict()
        self.__received_unacked: set[WSEvent] = set()

        self.__submitted_tasks: set[TN] = set()

        self.__queue: Queue[WSEvent] | None = None

        self.__close_future: Future[CloseCode] | None = None
        self.__close_task: TN | None = None

        self.__reader_task: TN | None = None

        self.__started: bool = False
        self.__closed: bool = False

        if start:
            self.start()

    # (...) -> Self is more precise here, but it confuses the type checker for some reason
    def __aiter__(self) -> AsyncIterator[WSEvent]:
        return self

    async def __anext__(self) -> WSEvent: ...

    @property
    def running(self) -> bool:
        return self.__started and not self.__closed

    @property
    def close_code(self) -> CloseCode | None:
        if self.__started and self.__close_future.done():
            return self.__close_future.result()

    def __get_close_code__(self) -> CloseCode:
        raw_code = self.__response.close_code

        if raw_code is None:
            return WSCloseCode.ABNORMAL_CLOSURE

        for cls in (WSCloseCode, CustomWSCloseCode):
            try:
                return cls(raw_code)
            except ValueError:
                continue

        return WSCloseCode.ABNORMAL_CLOSURE

    def __make_task__(self, coro: CN, /, *, wrap: bool) -> TN:
        if not self.running:
            raise RuntimeError(f"{type(self).__name__} is not running.")

        if wrap:
            real_coro = self.__wrap_coro__(coro)
        else:
            real_coro = coro

        return create_task(real_coro)

    async def __wrap_coro__(self, coro: CN, /) -> None:
        try:
            await coro

        except CancelledError:
            log(f"WebSocket task {coro} was cancelled.", DEBUG)
            raise

        except RatelimitException:
            log(f"WebSocket task {coro} exceeded a rate limit.", DEBUG)
            self.__signal_close__(WSCloseCode.POLICY_VIOLATION)

        except WSException as error:
            log(f"WebSocket task {coro} triggered closure ({error.code.value}).", DEBUG)
            self.__signal_close__(error.code)

        except Exception as error:
            log(f"WebSocket task {coro} raised an exception.", ERROR, error=error)
            self.__signal_close__(CustomWSCloseCode.InternalError)

    def __signal_close__(self, code: CloseCode, /) -> None:
        if not self.__close_future.done():
            self.__close_future.set_result(code)

    async def __wait_for_close__(self) -> None:
        code = await self.__close_future
        await self.close(code=code)

    async def __reader__(self) -> None:

        async for message in self.__response:

            if self.__ratelimited:
                check_ratelimit(self.__hits, limit=self.__limit, interval=self.__interval)

            custom_message = parse_received_message(message)

            if isinstance(custom_message, WSEvent):
                self.__receive_event__(custom_message)
                ...

            elif isinstance(custom_message, WSAck):
                self.__receive_ack__(custom_message)
                ...

            # The parser should never allow this to be reached
            else:
                raise RuntimeError(f"Encountered an unexpected message: {custom_message}.")

        # The underlying transport has closed
        # Get the transport's close code and set it as our close code
        self.__signal_close__(self.__get_close_code__())

    def __receive_event__(self, event: WSEvent, /) -> None: ...

    def __receive_ack__(self, ack: WSAck, /) -> None: ...

    def start(self) -> bool:
        if self.__started:
            return False

        self.__started = True

        self.__queue = Queue()

        self.__close_future = make_future()
        self.__close_task = self.__make_task__(self.__wait_for_close__(), wrap=False)

        self.__reader_task = self.__make_task__(self.__reader__(), wrap=True)

        return True

    async def close(self, *, code: CloseCode) -> bool:
        if not self.running:
            return False

        self.__closed = True

        await self.__response.close(code=code)

        # Guarantee that the future is set
        self.__signal_close__(code)

        ...

        self.__queue.shutdown()  # noqa

        return True
