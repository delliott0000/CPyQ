from __future__ import annotations

from typing import TYPE_CHECKING

from .bases import ComparesIDABC, ComparesIDMixin, JSONSerialisableABC
from .errors import SessionBound
from .resource import ResourceJSONVersion
from .state import State
from .utils import log

if TYPE_CHECKING:
    from typing import Any

    from .resource import Resource
    from .token import Token
    from .user import User
    from .WebSocket import WSProxy

    Json = dict[str, Any]

__all__ = ("Session",)


class Session(ComparesIDMixin, ComparesIDABC, JSONSerialisableABC):
    __slots__ = ("_id", "_user", "_state", "_resource", "_connections")

    def __init__(
        self,
        _id: str,
        user: User,
        /,
        *,
        state: State | None = None,
    ):
        self._id = _id
        self._user = user
        self._state = state if state is not None else State()
        self._resource = None
        self._connections = {}

    @property
    def id(self) -> str:
        return self._id

    @property
    def user(self) -> User:
        return self._user

    @property
    def state(self) -> State:
        return self._state

    @property
    def resource(self) -> Resource | None:
        return self._resource

    @property
    def bound(self) -> bool:
        return self._resource is not None

    @property
    def connections(self) -> dict[Token, WSProxy]:
        return self._connections

    @property
    def connected(self) -> bool:
        return bool(self._connections)

    def acquire_resource(self, resource: Resource, /) -> None:
        if not self.bound:
            resource.acquire(self)
            log(f"{self._user} acquired {resource}. (Session ID: {self._id})")
            self._resource = resource
        else:
            raise SessionBound(self, resource.id)

    def release_resource(self) -> None:
        if self.bound:
            self._resource.release(self)
            log(f"{self._user} released {self._resource}. (Session ID: {self._id})")
            self._resource = None

    def json(self) -> Json:
        try:
            resource = self._resource.json(version=ResourceJSONVersion.metadata)
        except AttributeError:
            resource = None

        return {
            "id": self._id,
            "user": self._user.json(),
            "state": self._state.json(),
            "resource": resource,
        }
