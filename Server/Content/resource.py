from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Protocol

from Common import ResourceLocked, ResourceNotOwned, SessionBound, log, now

if TYPE_CHECKING:
    from typing import Any, TypeVar

    from Common import SelfUser, Serialisable, Session, User

    Json = dict[str, Any]
    T = TypeVar("T")

__all__ = ("ResourceItem", "Resource")


class ResourceItem(Protocol):
    id: int
    owner: User

    metadata_type: type[Serialisable]
    preview_type: type[Serialisable]
    view_type: type[Serialisable]

    def decompose(self, target: type[T], /) -> T: ...


class Resource:
    __slots__ = ("__item", "__last_active", "__session")

    def __init__(self, item: ResourceItem, /):
        self.__item = item
        self.__reset__()

    def __str__(self):
        return str(self.__item)

    def __reset__(self) -> None:
        self.__last_active = now()
        self.__set_session__(None)

    def __set_session__(self, session: Session | None, /) -> None:
        self.__session = session

    @property
    def id(self) -> int:
        return self.__item.id

    @property
    def owner(self) -> User:
        return self.__item.owner

    @property
    def metadata(self) -> Serialisable:
        item = self.__item
        return item.decompose(item.metadata_type)

    @property
    def preview(self) -> Serialisable:
        item = self.__item
        return item.decompose(item.preview_type)

    @property
    def view(self) -> Serialisable:
        item = self.__item
        return item.decompose(item.view_type)

    @property
    def locked(self) -> bool:
        return self.__session is not None

    @property
    def last_active(self) -> datetime:
        return self.__last_active

    @property
    def current_user(self) -> SelfUser:
        if self.locked:
            return self.__session.user

    def is_idle(self, grace: timedelta, /) -> bool:
        return not self.locked and self.__last_active + grace < now()

    def lock(self, session: Session, /) -> None:
        if session.bound:
            raise SessionBound(session, self.id)
        elif self.locked:
            raise ResourceLocked(session, self.id)

        session.bind(self.id)
        self.__set_session__(session)
        log(f"{self} acquired by {session.user}.")

    def unlock(self, session: Session, /) -> None:
        self.ensure_acquired(session)

        session.unbind()
        self.__reset__()
        log(f"{self} released by {session.user}.")

    def ensure_acquired(self, session: Session, /) -> None:
        # Assume session == self.__session <=> session.resource_id == self.id
        if not self.locked or session != self.__session:
            raise ResourceNotOwned(session, self.id)
