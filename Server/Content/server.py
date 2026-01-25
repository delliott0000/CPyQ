from __future__ import annotations

from asyncio import Runner, gather
from contextlib import AsyncExitStack
from typing import TYPE_CHECKING

from aiohttp import WSCloseCode
from aiohttp.web import Application, AppRunner, TCPSite

from Common import log

from .auth_service import AuthService
from .manager import AutopilotManager
from .middlewares import middlewares
from .postgre_client import ServerPostgreSQLClient
from .resource_service import ResourceService
from .websocket_service import AutopilotWebSocketService, UserWebSocketService

if TYPE_CHECKING:
    from Common import Resource, ServerConfig, Session, Token, User

__all__ = ("Server",)


class Server:
    def __init__(self, *, config: ServerConfig):
        self.config = config

        self.db = ServerPostgreSQLClient(config=config.postgres)

        self.app = Application(middlewares=middlewares)
        self.runner: AppRunner | None = None

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

    def run(self) -> None:
        async def _service():
            log("Starting up service...")

            self.runner = AppRunner(self.app, access_log=None)
            await self.runner.setup()

            site = TCPSite(self.runner, self.config.host, self.config.port)
            await site.start()

            log("Service running.")

            services = self.services
            contexts = services + (self.db,)
            tasks = (service.task for service in services)

            async with AsyncExitStack() as stack:

                for context in contexts:
                    await stack.enter_async_context(context)

                await gather(*tasks)

        async def _cleanup():
            coros = (
                connection.close(code=WSCloseCode.GOING_AWAY)
                for session in self.session_id_to_session.values()
                for connection in session.connections.values()
            )
            await gather(*coros)
            await self.runner.cleanup()

        with Runner() as runner:
            try:
                runner.run(_service())
            except (KeyboardInterrupt, SystemExit):
                log("Received signal to terminate program.")
            finally:
                log("Cleaning up...")
                runner.run(_cleanup())
                log("Done. Have a nice day!")
