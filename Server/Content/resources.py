from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from Common import (
    IntIdentifiable,
    QuoteMetadata,
    QuotePreview,
    QuoteView,
    ResourceLocked,
    ResourceNotOwned,
    SerialisableCodec,
    SessionBound,
    User,
    log,
    now,
)

if TYPE_CHECKING:
    from datetime import datetime, timedelta
    from typing import Any, TypeVar

    from Common import SelfUser, Session

    ID = str | int
    Json = dict[str, Any]
    T = TypeVar("T")

__all__ = (
    "ResourceItem",
    "Resource",
    "QuoteMetadataResource",
    "QuotePreviewResource",
    "QuoteViewResource",
)


class ResourceItem(Protocol):
    id: ID
    owner: User
    metadata_type: type[...]
    preview_type: type[...]
    view_type: type[...]

    def decompose(self, target: type[T], /) -> T: ...
    def json(self) -> Json: ...


class Resource(IntIdentifiable):
    codecs = {
        "owner": SerialisableCodec(User),
    }

    owner: User

    # IMPORTANT: Add these into the __slots__ of each subclass!
    _session: Session | None
    _last_active: datetime

    def __init__(self, json: Json, /):
        super().__init__(json)
        self._reset()

    def _reset(self) -> None:
        self._set_session(None)
        self._last_active = now()

    def _set_session(self, session: Session | None, /):
        self._session = session

    @property
    def locked(self) -> bool:
        return self._session is not None

    @property
    def current_user(self) -> SelfUser | None:
        if self.locked:
            return self._session.user

    @property
    def last_active(self) -> datetime:
        return self._last_active

    def is_idle(self, grace: timedelta, /) -> bool:
        return not self.locked and self._last_active + grace < now()

    def lock(self, session: Session, /) -> None:
        if session.bound:
            raise SessionBound(session, self.id)
        elif self.locked:
            raise ResourceLocked(session, self.id)

        session.bind(self.id)
        self._set_session(session)
        log(f"{self} acquired by {session.user}.")

    def unlock(self, session: Session, /) -> None:
        self.ensure_acquired(session)

        session.unbind()
        self._reset()
        log(f"{self} released by {session.user}.")

    def ensure_acquired(self, session: Session, /) -> None:
        # Assume session == self._session <=> session.resource_id == self.id
        if not self.locked or session != self._session:
            raise ResourceNotOwned(session, self.id)


class QuoteMetadataResource(Resource, QuoteMetadata):
    __slots__ = ("_session", "_last_active")


class QuotePreviewResource(Resource, QuotePreview):
    __slots__ = ("_session", "_last_active")


class QuoteViewResource(Resource, QuoteView):
    __slots__ = ("_session", "_last_active")
