from __future__ import annotations

from datetime import datetime, timedelta
from secrets import token_urlsafe
from typing import TYPE_CHECKING

from .bases import ComparesIDABC, ComparesIDMixin
from .utils import decode_datetime, encode_datetime, now

if TYPE_CHECKING:
    from typing import Any

    from .session import Session

    Json = dict[str, Any]
    ExpirationType = datetime | timedelta | float | str


class Token(ComparesIDMixin, ComparesIDABC):
    __slots__ = (
        "_id",
        "_session",
        "_killed_at",
        "_access",
        "_refresh",
        "_access_expires",
        "_refresh_expires",
    )

    def __init__(
        self,
        session: Session,
        /,
        *,
        access: str | None = None,
        refresh: str | None = None,
        access_expires: ExpirationType,
        refresh_expires: ExpirationType,
        killed_at: datetime | None = None,
    ):
        self._id = token_urlsafe(32)
        self._session = session
        self._killed_at = killed_at
        self.renew(
            access=access,
            refresh=refresh,
            access_expires=access_expires,
            refresh_expires=refresh_expires,
            force=True,
        )

    @property
    def id(self) -> str:
        return self._id

    @property
    def session(self) -> Session:
        return self._session

    @property
    def killed(self) -> bool:
        return self._killed_at is not None

    @property
    def killed_at(self) -> datetime | None:
        return self._killed_at

    @property
    def access(self) -> str:
        return self._access

    @property
    def refresh(self) -> str:
        return self._refresh

    @property
    def access_expires(self) -> datetime:
        return self._access_expires

    @property
    def refresh_expires(self) -> datetime:
        return self._refresh_expires

    @property
    def active(self) -> bool:
        return not self.killed and self._access_expires > now()

    @property
    def expired(self) -> bool:
        return self.killed or self._refresh_expires < now()

    def kill(self) -> bool:
        if not self.expired:
            self._killed_at = now()

            return True
        else:
            return False

    def renew(
        self,
        *,
        access: str | None = None,
        refresh: str | None = None,
        access_expires: ExpirationType,
        refresh_expires: ExpirationType,
        force: bool = False,
    ) -> bool:
        if force or not self.expired:
            t = now()
            attrs = {}

            for attr, arg in (
                ("_access_expires", access_expires),
                ("_refresh_expires", refresh_expires),
            ):
                if isinstance(arg, datetime):
                    attrs[attr] = arg
                elif isinstance(arg, timedelta):
                    attrs[attr] = t + arg
                elif isinstance(arg, (float, int)):
                    attrs[attr] = t + timedelta(seconds=arg)
                elif isinstance(arg, str):
                    attrs[attr] = decode_datetime(arg)
                else:
                    raise TypeError("Expiration type not supported.")

            self._access = access or token_urlsafe(32)
            self._refresh = refresh or token_urlsafe(32)

            for attr in attrs:
                setattr(self, attr, attrs[attr])

            return True
        else:
            return False

    def to_json(self) -> Json:
        try:
            killed_at = encode_datetime(self._killed_at)
        except AttributeError:
            killed_at = None

        return {
            "access": self._access,
            "refresh": self._refresh,
            "access_expires": encode_datetime(self._access_expires),
            "refresh_expires": encode_datetime(self._refresh_expires),
            "killed_at": killed_at,
            "session": self._session.to_json(),
        }
