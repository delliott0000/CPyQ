from __future__ import annotations

from typing import TYPE_CHECKING

from ..errors import WSException
from ..utils import make_future
from .enums import HandshakePhase

if TYPE_CHECKING:
    from asyncio import Future

    from aiohttp import WSCloseCode

    from .enums import CustomWSCloseCode
    from .messages import WSEvent

    CloseCode = WSCloseCode | CustomWSCloseCode

__all__ = ("HandshakeContext",)


class HandshakeContext:
    __slots__ = ("__phase", "__event", "__future")

    def __init__(self):
        self.__phase: HandshakePhase = HandshakePhase.NotStarted
        self.__event: WSEvent | None = None
        self.__future: Future[WSEvent] = make_future()

    def __raise__(self, message: str, /) -> None:
        raise RuntimeError(f"{type(self).__name__} {message}.")

    def __ensure_mutable__(self) -> None:
        if self.__future.done():

            try:
                reason = self.__future.result()
            except Exception as error:
                reason = error

            self.__raise__(f"is immutable: {reason!r}")

    def bind(self, event: WSEvent) -> None:
        self.__ensure_mutable__()

        if self.__phase != HandshakePhase.NotStarted:
            self.__raise__("has already started")

        # In Progress <=> Event is set
        self.__phase = HandshakePhase.InProgress
        self.__event = event

    def done(self) -> None:
        self.__ensure_mutable__()

        if self.__phase != HandshakePhase.InProgress:
            self.__raise__("is not in progress")

        # Done <=> Future is set
        self.__phase = HandshakePhase.Done
        self.__future.set_result(self.__event)

    def fail(self, *, code: CloseCode) -> None:
        self.__ensure_mutable__()

        exception = WSException(code)
        self.__future.set_exception(exception)

    async def wait(self) -> WSEvent:
        return await self.__future
