from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .bases import ComparesIDFormattedABC, ComparesIDFormattedMixin, JSONSerialisableABC
from .errors import ResourceLocked, ResourceNotOwned
from .utils import now

if TYPE_CHECKING:
    from datetime import datetime, timedelta
    from typing import Any

    from .session import Session
    from .user import User

    Json = dict[str, Any]

__all__ = ("ResourceJSONVersion", "ResourceABC", "ResourceMixin", "Resource")


# fmt: off
class ResourceJSONVersion(Enum):
    metadata = 0
    preview  = 1
    view     = 2
    default  = metadata
# fmt: on


class ResourceABC(ComparesIDFormattedABC, JSONSerialisableABC, ABC):
    __slots__ = ()

    @property
    @abstractmethod
    def id(self) -> int:
        pass

    @property
    @abstractmethod
    def owner(self) -> User:
        pass

    @abstractmethod
    def json(self, *, version: ResourceJSONVersion = ResourceJSONVersion.default) -> Json:
        pass


class ResourceMixin(ComparesIDFormattedMixin):
    __slots__ = ()

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._reset()

    def _reset(self) -> None:
        self._set_session(None)
        self._last_active = now()  # noqa

    def _set_session(self, session: Session | None, /):
        self._session = session  # noqa

    @property
    def locked(self) -> bool:
        return self._session is not None

    @property
    def current_user(self) -> User | None:
        if self.locked:
            return self._session.user

    @property
    def last_active(self) -> datetime:
        return self._last_active

    def is_idle(self, grace: timedelta, /) -> bool:
        return not self.locked and self._last_active + grace < now()

    def acquire(self, session: Session, /) -> None:
        if self.locked:
            raise ResourceLocked(session, self.id)
        else:
            self._set_session(session)

    def release(self, session: Session, /) -> None:
        if not self.locked:
            return
        elif self._session != session:
            raise ResourceNotOwned(session, self.id)
        else:
            self._reset()

    def ensure_acquired(self, session: Session, /) -> None:
        if not self.locked or session != self._session:
            raise ResourceNotOwned(session, self.id)


@runtime_checkable
class Resource(Protocol):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("Resource can not be directly instantiated.")

    def __init_subclass__(cls, **kwargs: Any):
        raise TypeError("Inherit from (ResourceMixin, ResourceABC) instead.")

    @property
    def id(self) -> int: ...
    @property
    def formatted_id(self) -> str: ...
    @property
    def owner(self) -> User: ...
    @property
    def locked(self) -> bool: ...
    @property
    def current_user(self) -> User | None: ...
    @property
    def last_active(self) -> datetime: ...
    def is_idle(self, grace: timedelta, /) -> bool: ...
    def acquire(self, session: Session, /) -> None: ...
    def release(self, session: Session, /) -> None: ...
    def ensure_acquired(self, session: Session, /) -> None: ...
    def json(self, *, version: ResourceJSONVersion = ...) -> Json: ...
