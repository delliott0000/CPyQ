from __future__ import annotations

from typing import TYPE_CHECKING

from Common import log

if TYPE_CHECKING:
    from Common import Task, Token, WSProxy

__all__ = ("Autopilot", "AutopilotManager")


class Autopilot:
    __slots__ = ("__token",)

    def __init__(self, token: Token, /):
        self.__token = token

    def __str__(self):
        return f"Autopilot {self.__token.session.user} (Token ID: {self.__token.id})"

    @property
    def proxy(self) -> WSProxy:
        token = self.__token
        proxy = token.session.connections.get(token)

        if proxy is None:
            raise RuntimeError(f"{self} does not have a WebSocket proxy.")

        return proxy

    @property
    def connected(self) -> bool:
        try:
            return self.proxy.running
        except RuntimeError:
            return False

    @property
    def task(self) -> Task | None: ...


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
