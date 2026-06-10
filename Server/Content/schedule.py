from __future__ import annotations

from asyncio import Queue
from typing import TYPE_CHECKING

from Common import log

if TYPE_CHECKING:
    from collections.abc import Coroutine
    from typing import Any

    from Common import Task, Token, WSProxy

    CN = Coroutine[Any, Any, None]

__all__ = ("Autopilot", "AutopilotManager")


class Autopilot:
    __slots__ = ("__token", "__task")

    def __init__(self, token: Token, /):
        self.__token = token
        self.__task = None

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
    def task(self) -> Task | None:
        return self.__task

    @property
    def busy(self) -> bool:
        return self.__task is not None

    def set_task(self, task: Task, /) -> None:
        if self.busy:
            raise RuntimeError(f"{self} is busy.")

        self.__task = task

    def clear_task(self) -> Task:
        if not self.busy:
            raise RuntimeError(f"{self} is not busy.")

        previous_task = self.__task
        self.__task = None

        return previous_task


class AutopilotManager:
    def __init__(self):
        self.__autopilots: dict[Token, Autopilot] = {}
        self.__available: Queue[Autopilot] = Queue()
        self.__tasks: Queue[Task] = Queue()

    async def connect_autopilot(self, token: Token, /) -> None:
        autopilot = self.__autopilots[token] = Autopilot(token)

        if not autopilot.busy:
            await self.queue_autopilot(autopilot)

        log(f"{autopilot} connected.")

    async def disconnect_autopilot(self, token: Token, /) -> None:
        autopilot = self.__autopilots.pop(token)

        if autopilot.busy:
            await self.queue_task(autopilot.task)

        log(f"{autopilot} disconnected.")

    def get_autopilot(self, token: Token, /) -> Autopilot:
        return self.__autopilots[token]

    async def wait_for_autopilot(self) -> Autopilot:
        while True:
            autopilot = await self.__available.get()

            if autopilot.connected:
                return autopilot

    async def wait_for_task(self) -> Task:
        while True:
            task = await self.__tasks.get()

            if task.pending:
                return task

    def queue_autopilot(self, autopilot: Autopilot, /) -> CN:
        return self.__available.put(autopilot)

    def queue_task(self, task: Task, /) -> CN:
        return self.__tasks.put(task)
