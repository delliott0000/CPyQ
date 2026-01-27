from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

    from aiohttp import ClientResponse, WSMessage

    from .resource import Resource
    from .session import Session

    Json = dict[str, Any]

__all__ = (
    "HTTPException",
    "ValidationError",
    "ResourceConflict",
    "ResourceLocked",
    "SessionBound",
    "ResourceNotOwned",
    "RatelimitExceeded",
    "InvalidFrameType",
)


class HTTPException(Exception):
    def __init__(self, response: ClientResponse, data: Json, /):
        super().__init__(f"{response.status} {response.reason}")
        self.response = response
        self.data = data


class ValidationError(Exception):
    def __init__(self, results: set[str], /):
        super().__init__("\n".join(results))
        self.results = results


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


class RatelimitExceeded(Exception):
    def __init__(self, hits: list[float], /, *args: Any, limit: int, interval: float):
        super().__init__(*args)
        self.hits = hits
        self.limit = limit
        self.interval = interval


class InvalidFrameType(Exception):
    def __init__(self, message: WSMessage, /, *args: Any):
        super().__init__(*args)
        self.message = message
