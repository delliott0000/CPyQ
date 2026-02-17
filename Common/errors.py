from __future__ import annotations

from typing import TYPE_CHECKING

from .format import format_http

if TYPE_CHECKING:
    from enum import IntEnum
    from typing import Any

    from .resource import Resource
    from .session import Session

    Json = dict[str, Any]

__all__ = (
    "ResourceConflict",
    "ResourceLocked",
    "SessionBound",
    "ResourceNotOwned",
    "NetworkException",
    "HTTPException",
    "RatelimitException",
    "WSException",
)


class ResourceConflict(Exception):
    def __init__(self, session: Session, resource: Resource, /, *args: Any):
        super().__init__(*args)
        self.session = session  # The *requesting* session
        self.resource = resource  # The *requested* resource


class ResourceLocked(ResourceConflict):
    def __init__(self, session: Session, resource: Resource, /):
        super().__init__(
            session, resource, "Requested resource is already locked by another session."
        )


class SessionBound(ResourceConflict):
    def __init__(self, session: Session, resource: Resource, /):
        super().__init__(
            session, resource, "Requesting session is already bound to a resource."
        )


class ResourceNotOwned(ResourceConflict):
    def __init__(self, session: Session, resource: Resource, /):
        super().__init__(
            session, resource, "Requesting session is not bound to the requested resource."
        )


class NetworkException(Exception):
    pass


class RatelimitException(NetworkException):
    def __init__(
        self,
        hits: list[float],
        /,
        *,
        limit: int,
        interval: float,
    ):
        super().__init__(f"Rate limit {limit}/{interval}s exceeded.")
        self.hits = hits
        self.limit = limit
        self.interval = interval


class HTTPException(NetworkException):
    def __init__(
        self,
        headers: Json,
        status: int,
        reason: str | None,
        json: Json,
    ):
        super().__init__(format_http(status, reason))
        self.headers = headers
        self.status = status
        self.reason = reason
        self.json = json


class WSException(NetworkException):
    def __init__(
        self,
        code: IntEnum,
    ):
        super().__init__(f"{code.value} {code.name}")
        self.code = code
