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
    """
    The following statements (must) always hold true
    - self.__phase == InProgress or self.__phase == Done <=> self.__event is not None
    - self.__phase == Done <=> self.__future.result() successfully returns an instance of WSEvent
    - self.__future.exception() is not None => self.__phase != Done
    """

    __slots__ = ("__phase", "__event", "__future")

    def __init__(self):
        self.__phase: HandshakePhase = HandshakePhase.NotStarted
        self.__event: WSEvent | None = None
        self.__future: Future[WSEvent] = make_future()

    @property
    def event(self) -> WSEvent:
        if self.__event is None:
            self.__raise__("is not yet bound")
        return self.__event

    @property
    def is_done(self) -> bool:
        return self.__phase == HandshakePhase.Done

    @property
    def exception(self) -> WSException | None:
        return self.__future.exception()

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

        self.__phase = HandshakePhase.InProgress
        self.__event = event

    def done(self) -> None:
        self.__ensure_mutable__()

        if self.__phase != HandshakePhase.InProgress:
            self.__raise__("is not in progress")

        self.__phase = HandshakePhase.Done
        self.__future.set_result(self.__event)

    def fail(self, code: CloseCode, /) -> None:
        self.__ensure_mutable__()

        exception = WSException(code)
        self.__future.set_exception(exception)

    async def wait(self) -> WSEvent:
        return await self.__future
