from __future__ import annotations

from abc import ABC
from dataclasses import asdict
from typing import TYPE_CHECKING

from aiohttp import WSCloseCode
from aiohttp.web import HTTPConflict

from Common import (
    AutopilotHandshake,
    CustomWSResponse,
    HandshakeT,
    UserHandshake,
    build_payload,
    log,
)

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

    from Common import Token

__all__ = ("BaseWebSocketService", "UserWebSocketService", "AutopilotWebSocketService")


class BaseWebSocketService(BaseService, ABC):
    async def prepare_ws(
        self,
        request: Request,
        token: Token,
        /,
        *,
        handshake_cls: type[HandshakeT],
    ) -> CustomWSResponse[HandshakeT]:
        if token in token.session.connections:
            raise HTTPConflict(reason="Already connected")

        config = self.server.config

        response = CustomWSResponse(
            handshake_cls=handshake_cls,
            ratelimited=True,
            limit=config.ws_message_limit,
            interval=config.ws_message_interval,
            heartbeat=config.ws_heartbeat,
            max_msg_size=config.ws_max_message_size * 1024,
        )

        handshake_json = asdict(self.server.config.handshake_policy)
        handshake = build_payload(handshake_cls, handshake_json)
        response.handshake_manager.set_handshake(handshake)

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

    async def serve_ws(
        self,
        request: Request,
        /,
        *,
        handshake_cls: type[HandshakeT],
    ) -> CustomWSResponse[HandshakeT]:
        token = self.token_from_request(request)
        response = await self.prepare_ws(request, token, handshake_cls=handshake_cls)

        try:
            response.handshake_manager.set_wired()
            await response.send_payload(response.handshake_manager.handshake)

            async for _ in response:
                ...

        finally:
            await self.cleanup_ws(token)

        return response


class UserWebSocketService(BaseWebSocketService):
    async def task_coro(self) -> None:
        pass

    @route("get", "/ws/user")
    @ratelimit(limit=10, interval=60, bucket_type=BucketType.Token)
    @user_only
    @validate_access
    async def ws_user(self, request: Request, /) -> CustomWSResponse[UserHandshake]:
        return await self.serve_ws(request, handshake_cls=UserHandshake)


class AutopilotWebSocketService(BaseWebSocketService):
    async def task_coro(self) -> None:
        pass

    @route("get", "/ws/autopilot")
    @ratelimit(limit=10, interval=60, bucket_type=BucketType.Token)
    @autopilot_only
    @validate_access
    async def ws_autopilot(self, request: Request, /) -> CustomWSResponse[AutopilotHandshake]:
        return await self.serve_ws(request, handshake_cls=AutopilotHandshake)
