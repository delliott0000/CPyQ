from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from aiohttp import WSCloseCode
from aiohttp.web import HTTPConflict

from Common import CustomWSResponse, log

from .base_service import BaseService
from .decorators import (
    BucketType,
    autopilot_only,
    ratelimit,
    route,
    user_only,
    validate_access,
)

if TYPE_CHECKING:
    from aiohttp.web import Request

    from Common import Token, WSEvent

__all__ = ("BaseWebSocketService", "UserWebSocketService", "AutopilotWebSocketService")


class BaseWebSocketService(BaseService, ABC):
    async def prepare_ws(self, request: Request, token: Token, /) -> CustomWSResponse:
        if token in token.session.connections:
            raise HTTPConflict(reason="Already connected")

        config = self.server.config

        response = CustomWSResponse(
            ratelimited=True,
            limit=config.ws_message_limit,
            interval=config.ws_message_interval,
            heartbeat=config.ws_heartbeat,
            max_msg_size=config.ws_max_message_size * 1024,
        )
        token.session.connections[token] = response

        await response.prepare(request)
        log(f"Opened WebSocket for {token.session.user}. (Token ID: {token.id})")

        return response

    async def cleanup_ws(self, token: Token, /) -> None:
        response = token.session.connections.pop(token, None)
        if response is None:
            return

        code = response.close_code or WSCloseCode.OK
        await response.close(code=code)
        log(
            f"Closed WebSocket for {token.session.user}. "
            f"Received code {response.close_code}. (Token ID: {token.id})"
        )

    async def serve_ws(self, request: Request, /) -> CustomWSResponse:
        token = self.token_from_request(request)
        response = await self.prepare_ws(request, token)

        try:
            async for event in response:
                await self.process_event(response, event)  # noqa

        finally:
            await self.cleanup_ws(token)

        return response

    async def process_event(
        self,
        response: CustomWSResponse,
        event: WSEvent,
        /,
    ) -> None:
        pass


class UserWebSocketService(BaseWebSocketService):
    async def task_coro(self) -> None:
        pass

    @route("get", "/ws/user")
    @ratelimit(limit=10, interval=60, bucket_type=BucketType.Token)
    @user_only
    @validate_access
    async def ws_user(self, request: Request, /) -> CustomWSResponse:
        return await self.serve_ws(request)


class AutopilotWebSocketService(BaseWebSocketService):
    async def task_coro(self) -> None:
        pass

    @route("get", "/ws/autopilot")
    @ratelimit(limit=10, interval=60, bucket_type=BucketType.Token)
    @autopilot_only
    @validate_access
    async def ws_autopilot(self, request: Request, /) -> CustomWSResponse:
        return await self.serve_ws(request)
