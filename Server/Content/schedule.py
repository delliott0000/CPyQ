from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Common import Token

__all__ = ("Autopilot", "AutopilotManager")


class Autopilot:
    __slots__ = ("__token",)

    def __init__(self, token: Token, /):
        self.__token = token


class AutopilotManager:
    def __init__(self): ...

    async def autopilot_connect(self, token: Token, /) -> Autopilot | None: ...

    async def autopilot_disconnect(self, token: Token, /) -> Autopilot | None: ...
