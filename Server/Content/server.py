from __future__ import annotations

from asyncio import gather, run
from contextlib import AsyncExitStack
from typing import TYPE_CHECKING

from aiohttp import WSCloseCode
from aiohttp.web import Application, AppRunner, TCPSite

from Common import create_process_pool, log

from .auth_service import AuthService
from .manager import AutopilotManager
from .middlewares import middlewares
from .postgre_client import ServerPostgreSQLClient
from .resource_service import ResourceService
from .websocket_service import AutopilotWebSocketService, UserWebSocketService

if TYPE_CHECKING:
    from typing import Self

    from Common import Resource, ServerConfig, Session, Token, User

__all__ = ("Server",)


class Server:
    def __init__(self, *, config: ServerConfig):
        self.config = config

        self.process_pool = create_process_pool(max_workers=config.max_process_pool_workers)

        self.db = ServerPostgreSQLClient(config=config.postgres)

        self.app = Application(middlewares=middlewares)
        self.runner = AppRunner(self.app, access_log=None)

        self.services = (
            AuthService(self),
            ResourceService(self),
            UserWebSocketService(self),
            AutopilotWebSocketService(self),
        )

        self.apm = AutopilotManager(self)

        self.key_to_token: dict[str, Token] = {}
        self.user_to_tokens: dict[User, set[Token]] = {}
        self.session_id_to_session: dict[str, Session] = {}
        self.rtype_rid_to_resource: dict[tuple[str, int], Resource] = {}

    async def __aenter__(self) -> Self:
        await self.__start__()
        return self

    async def __aexit__(self, *_) -> None:
        await self.__stop__()

    async def __start__(self) -> None:
        await self.runner.setup()

        site = TCPSite(self.runner, self.config.host, self.config.port)
        await site.start()

        log("Service running.")

    async def __stop__(self) -> None:
        coros = (
            connection.close(code=WSCloseCode.GOING_AWAY)
            for session in self.session_id_to_session.values()
            for connection in session.connections.values()
        )
        await gather(*coros)

        await self.runner.cleanup()

        log("Service stopped.")

    async def start(self) -> None:

        with self.process_pool:

            async with self.db:

                async with self:

                    async with AsyncExitStack() as stack:

                        for service in self.services:
                            await stack.enter_async_context(service)

                        tasks = (service.task for service in self.services)
                        await gather(*tasks)

    def run(self) -> None:
        try:
            run(self.start())
        except (KeyboardInterrupt, SystemExit):
            log("Received signal to terminate program.")
