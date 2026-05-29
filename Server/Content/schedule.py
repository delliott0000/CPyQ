from __future__ import annotations

from typing import TYPE_CHECKING

from Common import log

if TYPE_CHECKING:
    from Common import Token

__all__ = ("Autopilot", "AutopilotManager")


class Autopilot:
    __slots__ = ("__token",)

    def __init__(self, token: Token, /):
        self.__token = token

    def __str__(self):
        return f"Autopilot {self.__token.session.user} (Token ID: {self.__token.id})"


class AutopilotManager:
    def __init__(self):
        self.__autopilots: dict[Token, Autopilot] = {}

    def autopilot_connect(self, token: Token, /) -> Autopilot | None:
        if token in self.__autopilots:
            return

        autopilot = self.__autopilots[token] = Autopilot(token)

        ...

        log(f"{autopilot} connected.")

        return autopilot

    def autopilot_disconnect(self, token: Token, /) -> Autopilot | None:
        if token not in self.__autopilots:
            return

        autopilot = self.__autopilots.pop(token)

        ...

        log(f"{autopilot} disconnected.")

        return autopilot
