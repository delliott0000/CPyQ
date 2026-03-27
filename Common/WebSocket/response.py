from __future__ import annotations

from asyncio import CancelledError, create_task, gather, get_running_loop, sleep
from logging import ERROR
from typing import TYPE_CHECKING

from aiohttp import ClientWebSocketResponse, WSCloseCode
from aiohttp.web import WebSocketResponse

from ..errors import RatelimitException, WSException
from ..utils import check_ratelimit, log, now, protocol_error
from .enums import CustomWSCloseCode
from .messages import WSAck, WSEvent, parse_received_message

if TYPE_CHECKING:
    from asyncio import Future, Task
    from collections.abc import Coroutine
    from enum import IntEnum
    from typing import Any

    from .payloads import Payload

    Coro = Coroutine[Any, Any, None]
    TN = Task[None]

__all__ = ("WSResponseMixin", "CustomWSResponse", "CustomClientWSResponse")


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
        self.__error_task: TN = self.__make_task__(self.__wait_for_close__(), wrapped=False)

    async def __anext__(self) -> WSEvent:
        try:
            while True:
                message = await super().__anext__()  # noqa

                if self.ratelimited:
                    check_ratelimit(self.__hits, limit=self.limit, interval=self.interval)

                custom_message = parse_received_message(message)

                if isinstance(custom_message, WSEvent):
                    self.__recv_event__(custom_message)
                    return custom_message

                elif isinstance(custom_message, WSAck):
                    self.__recv_ack__(custom_message)
                    continue

                # The parser should never allow this to be reached
                raise RuntimeError(f"Encountered an unexpected message: {custom_message}.")

        except StopAsyncIteration:
            raise
        except RatelimitException:
            await self.close(code=WSCloseCode.POLICY_VIOLATION)
        except WSException as error:
            await self.close(code=error.code)
        except Exception:
            await self.close(code=CustomWSCloseCode.InternalError)
            raise

        raise StopAsyncIteration

    def __recv_event__(self, event: WSEvent, /) -> None:
        if event.id in self.__recv_unacked:
            protocol_error(CustomWSCloseCode.DuplicateEventID)

        elif event.is_fatal:
            protocol_error(CustomWSCloseCode.FatalEvent)

        # TODO: implement payload contexts
        elif not ...:
            protocol_error(CustomWSCloseCode.BadPayloadContext)

        self.__recv_unacked.add(event.id)

        ack = WSAck.from_event_id(event.id)
        self.submit(self.__send_ack__(ack))

    def __recv_ack__(self, ack: WSAck, /) -> None:
        try:
            task = self.__sent_unacked.pop(ack.id)
            task.cancel()
        except KeyError:
            protocol_error(CustomWSCloseCode.UnknownEvent)

    def __make_task__(
        self,
        coro: Coro,
        /,
        *,
        wrapped: bool = True,
        **wrapper_kwargs: Any,  # These have no effect if wrapped is False
    ) -> TN:
        if wrapped:
            real_coro = self.__coro_wrapper__(coro, **wrapper_kwargs)
        else:
            real_coro = coro

        return create_task(real_coro)

    def __signal_close__(self, code: IntEnum, /) -> None:
        if not self.__error_futr.done():
            self.__error_futr.set_result(code)

    async def __ack_timeout__(self) -> None: ...

    async def __wait_for_close__(self) -> None:
        code = await self.__error_futr
        await self.close(_cancel_all=False, code=code)

    async def __coro_wrapper__(self, coro: Coro, /, *, log_cancellation: bool = True) -> None:
        try:
            await coro
        except CancelledError:
            if log_cancellation:
                log(f"WebSocket task {coro} was cancelled.")
            raise
        except WSException as error:
            self.__signal_close__(error.code)
        except Exception as error:
            log(f"WebSocket task {coro} raised an exception.", ERROR, error=error)
            self.__signal_close__(CustomWSCloseCode.InternalError)

    async def __send_event__(self, event: WSEvent, /) -> None:
        if event.id in self.__sent_unacked:
            raise RuntimeError(
                f"Cannot send event {event.id}: the event is already sent and pending acknowledgement."
            )

        task = self.__make_task__(self.__ack_timeout__(), log_cancellation=False)
        self.__sent_unacked[event.id] = task

        prepared_event = event.with_sent_at(now())
        await self.send_json(prepared_event.json())  # noqa

    async def __send_ack__(self, ack: WSAck, /) -> None:
        if ack.id not in self.__recv_unacked:
            raise RuntimeError(
                f"Cannot acknowledge event {ack.id}: the corresponding event is unknown or already acknowledged."
            )

        self.__recv_unacked.discard(ack.id)

        prepared_ack = ack.with_sent_at(now())
        await self.send_json(prepared_ack.json())  # noqa

    def submit(self, coro: Coro, /) -> None:
        task = self.__make_task__(coro)
        self.__submitted_tasks.add(task)
        task.add_done_callback(self.__submitted_tasks.discard)

    async def send_payload(self, payload: Payload, /, **kwargs: Any) -> None:
        event = WSEvent.from_payload(payload, **kwargs)
        await self.__send_event__(event)

    async def close(self, _cancel_all: bool = True, **kwargs: Any) -> bool:
        result = await super().close(**kwargs)  # noqa

        if result is True:
            # Catch any tasks that were just submitted
            await sleep(0)

            tasks = self.__submitted_tasks | set(self.__sent_unacked.values())

            if _cancel_all is True:
                tasks.add(self.__error_task)

            for task in tasks:
                task.cancel()

            await gather(*tasks, return_exceptions=True)

        return result


class CustomWSResponse(WSResponseMixin, WebSocketResponse):
    pass


class CustomClientWSResponse(WSResponseMixin, ClientWebSocketResponse):
    pass
