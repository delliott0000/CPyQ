from __future__ import annotations

from asyncio import get_running_loop
from typing import TYPE_CHECKING, Generic, TypeVar

from .payloads import Handshake

HandshakeT = TypeVar("HandshakeT", bound=Handshake)

if TYPE_CHECKING:
    from asyncio import Future

__all__ = ("HandshakeManager",)


class HandshakeManager(Generic[HandshakeT]):
    def __init__(self, *, cls: type[HandshakeT]):
        if cls is Handshake or not issubclass(cls, Handshake):
            raise ValueError("A subclass of Handshake is required.")

        self.__cls: type[HandshakeT] = cls
        self.__handshake: HandshakeT | None = None
        self.__wired: bool = False
        self.__done_futr: Future[HandshakeT] = get_running_loop().create_future()

    def __pre_check__(
        self,
        *,
        expect_handshake: bool | None = None,
        expect_wired: bool | None = None,
        expect_done: bool | None = None,
        expect_fail: bool | None = None,
    ) -> None: ...

    async def wait_for_done(self) -> HandshakeT:
        return await self.__done_futr
