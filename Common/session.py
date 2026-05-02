from __future__ import annotations

from typing import TYPE_CHECKING

from .bases import ComparesIDABC, ComparesIDMixin, JSONSerialisableABC
from .state import State

if TYPE_CHECKING:
    from typing import Any

    from .token import Token
    from .user import User
    from .WebSocket import WSProxy

    Json = dict[str, Any]

__all__ = ("Session",)


class Session(ComparesIDMixin, ComparesIDABC, JSONSerialisableABC):
    __slots__ = ("_id", "_user", "_state", "_resource_id", "_connections")

    def __init__(
        self,
        _id: str,
        user: User,
        /,
        *,
        state: State | None = None,
        resource_id: int | None = None,
    ):
        self._id = _id
        self._user = user
        self._state = state if state is not None else State()
        self._resource_id = resource_id
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
    def resource_id(self) -> int | None:
        return self._resource_id

    @property
    def bound(self) -> bool:
        return self._resource_id is not None

    @property
    def connections(self) -> dict[Token, WSProxy]:
        return self._connections

    @property
    def connected(self) -> bool:
        return bool(self._connections)

    def bind(self, resource_id: int, /) -> None:
        self._resource_id = resource_id

    def unbind(self) -> None:
        self._resource_id = None

    def json(self) -> Json:
        return {
            "id": self._id,
            "user": self._user.json(),
            "state": self._state.json(),
            "resource_id": self._resource_id,
        }
