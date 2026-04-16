from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from asyncio import Task
    from collections.abc import AsyncIterator, Coroutine
    from typing import Any

    from aiohttp import WSCloseCode, WSMessage

    from .enums import CustomWSCloseCode
    from .messages import WSEvent

    Json = dict[str, Any]
    CN = Coroutine[Any, Any, None]
    TN = Task[None]
    CloseCode = WSCloseCode | CustomWSCloseCode

__all__ = ("WSResponseType", "WSProxy")


class WSResponseType(Protocol):
    def __aiter__(self) -> AsyncIterator[WSMessage]: ...
    @property
    def close_code(self) -> CloseCode | None: ...
    async def send_json(self, json: Json, /) -> Any: ...
    async def close(self, *, code: CloseCode = ...) -> Any: ...


class WSProxy:
    __slots__ = (
        "__response",
        "__ratelimited",
        "__limit",
        "__interval",
        "__hits",
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

        ...

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
        return self.__response.close_code

    def __make_task__(self, coro: CN, /, *, wrap: bool) -> TN: ...

    async def __wrap_coro__(self, coro: CN, /) -> None: ...

    def start(self) -> bool:
        if self.__started:
            return False

        self.__started = True

        ...

        return True

    async def close(self, *, code: CloseCode, _cancel_close_task: bool = True) -> bool:
        if not self.running:
            return False

        self.__closed = True

        await self.__response.close(code=code)

        ...

        return True
