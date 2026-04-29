from __future__ import annotations

from abc import ABC
from dataclasses import asdict
from typing import TYPE_CHECKING

from aiohttp.web import HTTPConflict, WebSocketResponse

from Common import WSPeerRole, WSPeerScope, WSPeerType, WSProxy, build_payload, log

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
    from typing import ClassVar

    from aiohttp.web import Request

    from Common import Handshake, Token

__all__ = ("BaseWebSocketService", "UserWebSocketService", "AutopilotWebSocketService")


class BaseWebSocketService(BaseService, ABC):
    PEER_TYPE: ClassVar[WSPeerType]

    def build_handshake(self, proxy: WSProxy, /) -> Handshake:
        cls = proxy.handshake_cls
        json = asdict(self.server.config.handshake_policy)
        return build_payload(cls, json)

    async def prepare_ws(
        self, request: Request, token: Token, /
    ) -> tuple[WSProxy, WebSocketResponse]:
        if token in token.session.connections:
            raise HTTPConflict(reason="Already connected")

        config = self.server.config

        response = WebSocketResponse(
            heartbeat=config.ws_heartbeat,
            max_msg_size=config.ws_max_message_size * 1024,
        )

        await response.prepare(request)
        log(f"Opened WebSocket for {token.session.user}. (Token ID: {token.id})")

        scope = WSPeerScope(
            role=WSPeerRole.Server,
            type=self.PEER_TYPE,
        )

        proxy = WSProxy(
            response,  # noqa
            scope=scope,
            ratelimited=True,
            limit=config.ws_message_limit,
            interval=config.ws_message_interval,
            start=True,
        )

        token.session.connections[token] = proxy

        return proxy, response

    def cleanup_ws(self, token: Token, /) -> None:
        proxy = token.session.connections.pop(token, None)

        if proxy is not None:
            log(
                f"Closed WebSocket for {token.session.user} "
                f"with code {proxy.close_code}. (Token ID: {token.id})"
            )

    async def serve_ws(self, request: Request, /) -> WebSocketResponse:
        token = self.token_from_request(request)
        proxy, response = await self.prepare_ws(request, token)

        try:
            async for _ in proxy:
                ...

        finally:
            self.cleanup_ws(token)

        return response


class UserWebSocketService(BaseWebSocketService):
    PEER_TYPE = WSPeerType.User

    async def task_coro(self) -> None:
        pass

    @route("get", "/ws/user")
    @ratelimit(limit=10, interval=60, bucket_type=BucketType.Token)
    @user_only
    @validate_access
    async def ws_user(self, request: Request, /) -> WebSocketResponse:
        return await self.serve_ws(request)


class AutopilotWebSocketService(BaseWebSocketService):
    PEER_TYPE = WSPeerType.Autopilot

    async def task_coro(self) -> None:
        pass

    @route("get", "/ws/autopilot")
    @ratelimit(limit=10, interval=60, bucket_type=BucketType.Token)
    @autopilot_only
    @validate_access
    async def ws_autopilot(self, request: Request, /) -> WebSocketResponse:
        return await self.serve_ws(request)
