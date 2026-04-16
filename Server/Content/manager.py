from __future__ import annotations

from asyncio import Condition
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Common import Token, WSProxy

    from .server import Server

__all__ = ("AutopilotInstance", "AutopilotManager")


class AutopilotInstance:
    __slots__ = ("__token", "__task_id")

    def __init__(self, token: Token, /):
        self.__token = token
        self.__task_id: int | None = None

    def __str__(self):
        return f"Autopilot {self.__token.session.user} (Token ID: {self.__token.id})"

    @property
    def ws(self) -> WSProxy:
        proxy = self.__token.session.connections.get(self.__token)
        if proxy is None or not proxy.running:
            raise RuntimeError(f"{self} is not connected.")
        else:
            return proxy

    @property
    def busy(self) -> bool:
        return self.__task_id is not None

    @property
    def task_id(self) -> int | None:
        return self.__task_id

    def set_task(self, task_id: int, /) -> None:
        if self.busy:
            raise RuntimeError(f"{self} is busy.")
        else:
            self.__task_id = task_id

    def clear_task(self) -> int:
        if not self.busy:
            raise RuntimeError(f"{self} is not busy.")
        else:
            last_task_id = self.__task_id
            self.__task_id = None
            return last_task_id


class AutopilotManager:
    def __init__(self, server: Server, /):
        self.__server = server
        self.__task_queue: list[int] = []
        self.__autopilots: dict[Token, AutopilotInstance] = {}
        self.__condition = Condition()

    @property
    def autopilot_count(self) -> int:
        return len(self.__autopilots)

    def queue_task(self, task_id: int, /) -> None:
        if task_id in self.__task_queue:
            raise ValueError(f"Task {task_id} is already queued.")
        else:
            self.__task_queue.append(task_id)

    def get_next_task(self) -> int | None:
        try:
            return self.__task_queue.pop(0)
        except IndexError:
            return None

    def get_autopilot(self) -> AutopilotInstance | None:
        for autopilot in self.__autopilots.values():
            if not autopilot.busy:
                return autopilot

    async def autopilot_connect(self, token: Token, /) -> None: ...

    async def autopilot_disconnect(self, token: Token, /) -> None: ...

    async def autopilot_task_done(self, token: Token, /) -> None: ...

    async def wait_for_autopilot(self) -> AutopilotInstance:
        async with self.__condition:
            return await self.__condition.wait_for(self.get_autopilot)
