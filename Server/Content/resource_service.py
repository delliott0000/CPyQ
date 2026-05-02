from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from aiohttp.web import (
    HTTPBadRequest,
    HTTPConflict,
    HTTPException,
    HTTPForbidden,
    HTTPNotFound,
    json_response,
)

from Common import (
    PermissionType,
    ResourceConflict,
    ResourceJSONVersion,
    ResourceLocked,
    ResourceNotOwned,
    Session,
    SessionBound,
    log,
)

from .base_service import BaseService
from .decorators import BucketType, ratelimit, route, user_only, validate_access
from .resources import QuoteResource

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine
    from typing import Any

    from aiohttp.web import Request, Response

    from Common import User

    from .resources import Resource

    Json = dict[str, Any]
    RLoader = Callable[[int], Coroutine[Any, Any, Resource]]

__all__ = ("ResourceService",)


class ResourceService(BaseService):
    async def task_coro(self) -> None:
        cache = self.server.resource_id_to_resource
        grace = timedelta(seconds=self.server.config.resource_grace)

        for resource_id in list(cache):
            resource = cache[resource_id]

            if resource.is_idle(grace):
                cache.pop(resource_id)
                last_active = resource.last_active.strftime("%Y-%m-%d %H:%M:%S")
                log(f"Resource {resource} unloaded. Last active at {last_active}.")

    @property
    def resource_map(self) -> dict[str, RLoader]:
        return {"quote": self.load_quote}  # noqa

    async def load_quote(self, quote_id: int, /) -> QuoteResource:
        quote = await self.server.db.get_quote(quote_id, cls=QuoteResource)

        if quote is None:
            raise HTTPNotFound(reason="Quote does not exist")

        return quote

    def convert_conflict(self, error: ResourceConflict, extra_data: Json, /) -> HTTPConflict:
        return self.attach_extra_data(HTTPConflict(reason=str(error).strip(".")), extra_data)

    def permission_check(
        self, user: User, resource: Resource, permission_type: PermissionType, /
    ) -> None:
        if not user.has_permission_from(permission_type, resource.owner):
            raise self.attach_extra_data(
                HTTPForbidden(reason="Missing required permission"),
                {"permission": permission_type.value},
            )

    def acquisition_check(self, session: Session, resource: Resource, /) -> None:
        try:
            resource.ensure_acquired(session)
        except ResourceNotOwned as error:
            raise self.convert_conflict(error, {"session": session.json()})

    async def load_resource(self, request: Request, /) -> Resource:
        resource_type = request.match_info["rtype"]
        resource_id = request.match_info["rid"]

        extra_data = {
            "resource_type": resource_type,
            "resource_id": resource_id,
        }

        try:
            resource_id = int(resource_id)
        except ValueError:
            raise self.attach_extra_data(
                HTTPBadRequest(reason="Resource ID must be an integral string"),
                extra_data,
            )

        cache = self.server.resource_id_to_resource

        cached = cache.get(resource_id)
        if cached is not None:
            return cached

        try:
            loader = self.resource_map[resource_type]
        except KeyError:
            raise self.attach_extra_data(
                HTTPBadRequest(reason="Unknown resource type"), extra_data
            )

        try:
            resource = await loader(resource_id)
        except HTTPException as error:
            raise self.attach_extra_data(error, extra_data)

        cache[resource_id] = resource

        log(f"Resource {resource} loaded.")

        return resource

    async def get_resource_and_session(self, request: Request, /) -> tuple[Resource, Session]:
        resource = await self.load_resource(request)
        session = self.session_from_request(request)
        return resource, session

    def ok_response(
        self,
        resource: Resource,
        /,
        *,
        version: ResourceJSONVersion = ResourceJSONVersion.default,
    ) -> Response:
        return json_response(
            {
                "message": "OK",
                "resource": resource.json(version=version),
            },
            status=200,
        )

    @route("post", "/resource/{rtype}/{rid}/acquire")
    @ratelimit(limit=10, interval=60, bucket_type=BucketType.User)
    @user_only
    @validate_access
    async def acquire(self, request: Request, /) -> Response:
        resource, session = await self.get_resource_and_session(request)

        self.permission_check(session.user, resource, PermissionType.acquire)
        # No acquisition check necessary

        try:
            resource.lock(session)
        except ResourceLocked as error:
            raise self.convert_conflict(error, {"locked_by": str(resource.current_user)})
        except SessionBound as error:
            raise self.convert_conflict(error, {"session": session.json()})

        return self.ok_response(resource)

    @route("post", "/resource/{rtype}/{rid}/release")
    @ratelimit(limit=10, interval=60, bucket_type=BucketType.User)
    @user_only
    @validate_access
    async def release(self, request: Request, /) -> Response:
        resource, session = await self.get_resource_and_session(request)

        # No permission check necessary
        # No acquisition check necessary

        try:
            resource.unlock(session)
        except ResourceNotOwned as error:
            raise self.convert_conflict(error, {"session": session.json()})

        return self.ok_response(resource)

    @route("get", "/resource/{rtype}/{rid}/preview")
    @ratelimit(limit=10, interval=60, bucket_type=BucketType.User)
    @user_only
    @validate_access
    async def preview(self, request: Request, /) -> Response:
        resource, session = await self.get_resource_and_session(request)

        self.permission_check(session.user, resource, PermissionType.preview)
        # No acquisition check necessary

        return self.ok_response(resource, version=ResourceJSONVersion.preview)

    @route("get", "/resource/{rtype}/{rid}/view")
    @ratelimit(limit=10, interval=60, bucket_type=BucketType.User)
    @user_only
    @validate_access
    async def view(self, request: Request, /) -> Response:
        resource, session = await self.get_resource_and_session(request)

        self.permission_check(session.user, resource, PermissionType.view)
        self.acquisition_check(session, resource)

        return self.ok_response(resource, version=ResourceJSONVersion.view)
