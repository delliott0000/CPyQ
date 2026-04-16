from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing import Any

    from aiohttp import WSCloseCode, WSMessage

    from .enums import CustomWSCloseCode
    from .messages import WSEvent

    Json = dict[str, Any]
    CloseCode = WSCloseCode | CustomWSCloseCode

__all__ = ("WSResponseType", "WSProxy")


class WSResponseType(Protocol):
    def __aiter__(self) -> AsyncIterator[WSMessage]: ...
    @property
    def close_code(self) -> CloseCode | None: ...
    async def send_json(self, json: Json, /) -> Any: ...
    async def close(self, *, code: CloseCode = ...) -> Any: ...


class WSProxy:
    __slots__ = ()

    def __init__(
        self,
        response: WSResponseType,
        /,
        *,
        ratelimited: bool = False,
        limit: int | None = None,
        interval: float | None = None,
        start: bool = False,
    ): ...

    # (...) -> Self is more precise here, but it confuses the type checker for some reason
    def __aiter__(self) -> AsyncIterator[WSEvent]: ...

    async def __anext__(self) -> WSEvent: ...

    @property
    def running(self) -> bool: ...

    @property
    def close_code(self) -> CloseCode | None: ...

    def start(self) -> bool: ...

    async def close(self, *, code: CloseCode) -> bool: ...
