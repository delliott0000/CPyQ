from __future__ import annotations

from secrets import token_urlsafe
from typing import TYPE_CHECKING

from .bases import StrIdentifiable
from .codecs import PrimitiveCodec, SerialisableCodec
from .state import State
from .user import SelfUser

if TYPE_CHECKING:
    from typing import Any, Self

    from .token import Token
    from .WebSocket import WSProxy

    Json = dict[str, Any]

__all__ = ("Session",)


class Session(StrIdentifiable):
    codecs = {
        "user": SerialisableCodec(SelfUser),
        "state": SerialisableCodec(State),
        "resource_id": PrimitiveCodec(int, optional=True),
    }

    user: SelfUser
    state: State
    resource_id: int | None

    __slots__ = ("_connections",)

    def __init__(self, json: Json, /):
        super().__init__(json)
        self._connections = {}

    @property
    def bound(self) -> bool:
        return self.resource_id is not None

    @property
    def connections(self) -> dict[Token, WSProxy]:
        return self._connections

    @property
    def connected(self) -> bool:
        return bool(self._connections)

    def bind(self, resource_id: int, /) -> None:
        self.resource_id = resource_id

    def unbind(self) -> None:
        self.resource_id = None

    @classmethod
    def new(cls, user: SelfUser, /) -> Self:
        json = {
            "id": token_urlsafe(16),
            "user": user.json(),
            "state": State.new().json(),
            "resource_id": None,
        }
        return cls(json)
