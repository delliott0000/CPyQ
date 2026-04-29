from __future__ import annotations

from asyncio import QueueShutDown  # noqa
from asyncio import (
    CancelledError,
    Queue,
    create_task,
    gather,
    sleep,
)
from logging import DEBUG, ERROR
from typing import TYPE_CHECKING, Protocol

from aiohttp import WSCloseCode

from ..errors import RatelimitException, WSException
from ..utils import check_ratelimit, log, make_future, now, protocol_error
from .enums import CustomWSCloseCode, WSPeerRole
from .handshake import HandshakeContext
from .messages import WSAck, WSEvent, parse_received_message
from .payloads import peer_type_to_handshake_cls

if TYPE_CHECKING:
    from asyncio import Future, Task
    from collections.abc import AsyncIterator, Coroutine
    from typing import Any

    from aiohttp import WSMessage

    from .enums import WSPeerScope
    from .messages import CustomWSMessage
    from .payloads import Handshake, Payload

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
        "__scope",
        "__ratelimited",
        "__limit",
        "__interval",
        "__hits",
        "__handshake_ctx",
        "__sent_unacked",
        "__received_unacked",
        "__submitted_tasks",
        "__fatal_event",
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
        scope: WSPeerScope,
        ratelimited: bool = False,
        limit: int | None = None,
        interval: float | None = None,
        start: bool = False,
    ):
        if ratelimited and (limit is None or interval is None):
            raise TypeError("Limit and interval must both be specified.")

        self.__response = response

        self.__scope = scope

        self.__ratelimited = ratelimited
        self.__limit = limit
        self.__interval = interval
        self.__hits: list[float] = []

        self.__handshake_ctx: HandshakeContext = HandshakeContext()

        self.__sent_unacked: dict[str, TN] = dict()
        self.__received_unacked: set[str] = set()

        self.__submitted_tasks: set[TN] = set()

        self.__fatal_event: WSEvent | None = None

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

    async def __anext__(self) -> WSEvent:
        if not self.__started:
            raise RuntimeError(f"{type(self).__name__} has not started.")

        try:
            return await self.__queue.get()

        except QueueShutDown:
            raise StopAsyncIteration

    @property
    def server(self) -> bool:
        return self.__scope.role == WSPeerRole.Server

    @property
    def running(self) -> bool:
        return self.__started and not self.__closed

    def __ensure_running__(self) -> None:
        if not self.running:
            raise RuntimeError(f"{type(self).__name__} is not running.")

    @property
    def handshake_cls(self) -> type[Handshake]:
        return peer_type_to_handshake_cls(self.__scope.type)

    def is_handshake(self, payload: Payload) -> bool:
        return type(payload) is self.handshake_cls

    @property
    def handshake_set(self) -> bool:
        return self.__handshake_ctx.event is not None

    @property
    def handshake_done(self) -> bool:
        return self.__handshake_ctx.is_done

    @property
    def handshake(self) -> Handshake:
        event = self.__handshake_ctx.event

        if event is None:
            raise RuntimeError("Handshake is not set.")

        return event.payload  # noqa

    async def wait_for_handshake(self) -> Handshake:
        event = await self.__handshake_ctx.wait()

        return event.payload  # noqa

    @property
    def fatal_event(self) -> WSEvent | None:
        return self.__fatal_event

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

    def __make_task__(self, coro: CN, /, *, wrap: bool, **wrap_kwargs: Any) -> TN:
        self.__ensure_running__()

        if wrap_kwargs and not wrap:
            raise ValueError("Wrap keyword arguments passed for a non-wrapped task.")

        if wrap:
            real_coro = self.__wrap_coro__(coro, **wrap_kwargs)
        else:
            real_coro = coro

        return create_task(real_coro)

    async def __wrap_coro__(self, coro: CN, /, *, log_cancellation: bool = True) -> None:
        try:
            await coro

        except CancelledError:
            if log_cancellation:
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
                result = self.__receive_event__(custom_message)

                if result:
                    await self.__queue.put(custom_message)

            elif isinstance(custom_message, WSAck):
                self.__receive_ack__(custom_message)

            # The parser should never allow this to be reached
            else:
                raise RuntimeError(f"Encountered an unexpected message: {custom_message}.")

        # The underlying transport has closed
        # Get the transport's close code and set it as our close code
        self.__signal_close__(self.__get_close_code__())

    def __receive_event__(self, event: WSEvent, /) -> bool:
        if event.id in self.__received_unacked:
            protocol_error(CustomWSCloseCode.DuplicateEventID)

        elif event.is_fatal:
            self.__fatal_event = event
            protocol_error(CustomWSCloseCode.FatalEvent)

        elif not event.payload.valid_context(receiver=self):
            protocol_error(CustomWSCloseCode.BadPayloadContext)

        self.__received_unacked.add(event.id)

        is_handshake = self.is_handshake(event.payload)

        if is_handshake:
            self.__handshake_ctx.bind(event)

        ack = WSAck.from_event(event)
        coro = self.__send_ack__(ack, is_handshake=is_handshake)
        self.submit(coro)

        # Don't enqueue the handshake event
        return not is_handshake

    def __receive_ack__(self, ack: WSAck, /) -> None: ...

    async def __send__(self, message: CustomWSMessage, /) -> CustomWSMessage:
        self.__ensure_running__()

        prepared_message = message.with_sent_at(now())
        await self.__response.send_json(prepared_message.json())

        return prepared_message

    async def __send_event__(self, event: WSEvent, /) -> None: ...

    async def __send_ack__(self, ack: WSAck, /, *, is_handshake: bool) -> None:
        await self.__send__(ack)

        self.__received_unacked.discard(ack.id)

        if is_handshake:
            self.__handshake_ctx.done()

    async def __ack_timeout__(self) -> None: ...

    def start(self) -> bool:
        if self.__started:
            return False

        self.__started = True

        self.__queue = Queue()

        self.__close_future = make_future()
        self.__close_task = self.__make_task__(self.__wait_for_close__(), wrap=False)

        self.__reader_task = self.__make_task__(self.__reader__(), wrap=True)

        return True

    def submit(self, coro: CN, /) -> TN:
        task = self.__make_task__(coro, wrap=True)

        self.__submitted_tasks.add(task)
        task.add_done_callback(self.__submitted_tasks.discard)

        return task

    async def close(self, *, code: CloseCode) -> bool:
        if not self.running:
            return False

        self.__closed = True

        # It is assumed that this is safe to call many times
        await self.__response.close(code=code)

        # Guarantee that the close future is set and that the close task will unblock
        # Don't await the task, otherwise it will deadlock
        self.__signal_close__(code)

        # Wake up the handshake future with an exception
        # If the handshake has complete (or failed for some reason), ignore and continue
        try:
            self.__handshake_ctx.fail(code)
        except RuntimeError:
            pass

        # Surpress the "Future exception was never retrieved" warning
        try:
            await self.__handshake_ctx.wait()
        except WSException:
            pass

        # Allow newly created coroutines to start before cancelling the tasks that schedule them
        # This will prevent "... was never awaited" warnings
        await sleep(0)

        tasks = set(self.__sent_unacked.values()) | self.__submitted_tasks

        for task in tasks:
            task.cancel()

        # The reader task will soon run to completion naturally, so there's no need to cancel it
        # But it should be allowed to finish before shutting down the message queue
        tasks.add(self.__reader_task)

        await gather(*tasks, return_exceptions=True)

        self.__queue.shutdown()  # noqa

        return True
