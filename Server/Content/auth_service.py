from __future__ import annotations

from asyncio import gather
from secrets import token_urlsafe
from typing import TYPE_CHECKING

from aiohttp.web import HTTPBadRequest, HTTPUnauthorized, json_response

from Common import CustomWSCloseCode, Session, Token, check_password, log, to_json

from .base_service import BaseService
from .decorators import BucketType, ratelimit, route, validate_access

if TYPE_CHECKING:
    from aiohttp.web import Request, Response

__all__ = ("AuthService",)


DUMMY_HASH = "$2b$12$9sVei45B23z0M.gV2EI4cunVKdBC2xu64pRAKqTHDnVPOWD8HHBQu"


class AuthService(BaseService):
    def add_token_keys(self, token: Token, /) -> None:
        self.server.key_to_token[token.access] = token
        self.server.key_to_token[token.refresh] = token

    def pop_token_keys(self, token: Token, /) -> None:
        self.server.key_to_token.pop(token.access, None)
        self.server.key_to_token.pop(token.refresh, None)

    def ok_response(self, token: Token, /) -> Response:
        return json_response(
            {
                "message": "OK",
                "token": token.to_json(),
            },
            status=200,
        )

    async def task_coro(self) -> None:
        key_to_token = self.server.key_to_token
        user_to_tokens = self.server.user_to_tokens
        session_id_to_session = self.server.session_id_to_session

        expired_cons = set()

        for key in list(key_to_token):
            try:
                token = key_to_token[key]
            except KeyError:
                continue
            if not token.expired:
                continue

            self.pop_token_keys(token)

            cons = token.session.connections
            user = token.session.user

            expired_cons.add(cons.get(token))

            if user in user_to_tokens:
                user_to_tokens[user].discard(token)
                log(f"Token discarded for {user}. (Token ID: {token.id})")

        for user in list(user_to_tokens):
            try:
                tokens = user_to_tokens[user]
            except KeyError:
                continue

            if not tokens:
                user_to_tokens.pop(user, None)
                log(f"Discarded empty token set for {user}.")

        expired_cons.discard(None)
        coros = (con.close(code=CustomWSCloseCode.TokenExpired) for con in expired_cons)
        await gather(*coros)

        for session_id in list(session_id_to_session):
            try:
                session = session_id_to_session[session_id]
            except KeyError:
                continue

            if not session.connected:
                session.release_resource()

            if session.user not in user_to_tokens:
                session_id_to_session.pop(session_id, None)
                log(f"Session discarded for {session.user}. (Session ID: {session_id})")

    @route("post", "/auth/login")
    @ratelimit(limit=10, interval=60, bucket_type=BucketType.IP)
    @ratelimit(limit=1000, interval=60, bucket_type=BucketType.Route)
    async def login(self, request: Request, /) -> Response:
        data = await to_json(request)

        username = data.get("username")
        password = data.get("password")

        if not isinstance(username, str) or not isinstance(password, str):
            raise HTTPBadRequest(reason="Missing or invalid username/password")

        user = await self.server.db.get_user(username=username)

        hashed_password = DUMMY_HASH if user is None else user.hashed_password
        correct = await self.server.process_pool.submit_async(
            check_password,
            password,
            hashed_password,
        )

        if user is None or not correct:
            raise HTTPUnauthorized(reason="Incorrect username/password")

        tokens = self.server.user_to_tokens.setdefault(user, set())
        if len(tokens) >= self.server.config.max_tokens_per_user:
            raise HTTPUnauthorized(reason="Too many unexpired tokens")

        try:
            session = self.server.session_id_to_session[data["session_id"]]
            if session.user != user:
                raise ValueError("Invalid session ID.")

        except (KeyError, ValueError):
            session = Session(token_urlsafe(16), user)
            self.server.session_id_to_session[session.id] = session
            log(f"Session issued for {user}. (Session ID: {session.id})")

        token = Token(
            session,
            access_expires=self.server.config.access_time,
            refresh_expires=self.server.config.refresh_time,
        )
        tokens.add(token)
        self.add_token_keys(token)
        log(f"Token issued for {user}. (Token ID: {token.id})")

        return self.ok_response(token)

    @route("post", "/auth/refresh")
    @ratelimit(limit=10, interval=60, bucket_type=BucketType.IP)
    @ratelimit(limit=10, interval=60, bucket_type=BucketType.Token)
    async def refresh(self, request: Request, /) -> Response:
        data = await to_json(request)

        refresh = data.get("refresh")
        self.check_key(refresh, for_refresh=True)

        token = self.server.key_to_token[refresh]
        self.pop_token_keys(token)
        token.renew(
            access_expires=self.server.config.access_time,
            refresh_expires=self.server.config.refresh_time,
        )
        self.add_token_keys(token)
        log(f"Token renewed for {token.session.user}. (Token ID: {token.id})")

        return self.ok_response(token)

    @route("post", "/auth/logout")
    @ratelimit(limit=10, interval=60, bucket_type=BucketType.IP)
    @ratelimit(limit=10, interval=60, bucket_type=BucketType.User)
    @validate_access
    async def logout(self, request: Request, /) -> Response:
        token = self.token_from_request(request)
        token.kill()
        log(f"Token killed for {token.session.user}. (Token ID: {token.id})")
        return self.ok_response(token)
