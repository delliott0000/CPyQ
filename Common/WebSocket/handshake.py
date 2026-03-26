from __future__ import annotations

from asyncio import get_running_loop
from typing import TYPE_CHECKING, Generic, TypeVar

from .payloads import Handshake

if TYPE_CHECKING:
    from asyncio import Future

    from ..errors import WSException

__all__ = ("HandshakeT", "HandshakeManager")


HandshakeT = TypeVar("HandshakeT", bound=Handshake)


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
    ) -> None:
        pairs = (
            ("Handshake", expect_handshake, self.has_handshake),
            ("Wired", expect_wired, self.is_wired),
            ("Done", expect_done, self.is_done),
            ("Fail", expect_fail, self.is_fail),
        )
        for name, expected, actual in pairs:
            if expected is not None and expected != actual:
                raise RuntimeError(f"{name} state mismatch; expected {expected}, got {actual}.")

    @property
    def has_handshake(self) -> bool:
        return self.__handshake is not None

    def set_handshake(self, handshake: HandshakeT, /) -> None:
        if not isinstance(handshake, self.__cls):
            raise TypeError(f"An instance of {self.__cls.__name__} is required.")

        self.__pre_check__(expect_handshake=False, expect_fail=False)
        self.__handshake = handshake

    @property
    def is_wired(self) -> bool:
        return self.__wired

    def set_wired(self) -> None:
        self.__pre_check__(expect_handshake=True, expect_wired=False, expect_fail=False)
        self.__wired = True

    @property
    def is_done(self) -> bool:
        return self.__done_futr.done() and self.__done_futr.exception() is None

    def set_done(self) -> None:
        self.__pre_check__(expect_wired=True, expect_done=False, expect_fail=False)
        self.__done_futr.set_result(self.__handshake)

    @property
    def is_fail(self) -> bool:
        return self.__done_futr.done() and self.__done_futr.exception() is not None

    def set_fail(self, error: WSException, /) -> None:
        self.__pre_check__(expect_done=False, expect_fail=False)
        self.__done_futr.set_exception(error)

    @property
    def handshake(self) -> HandshakeT:
        self.__pre_check__(expect_handshake=True, expect_fail=False)
        return self.__handshake

    async def wait_for_done(self) -> HandshakeT:
        return await self.__done_futr
