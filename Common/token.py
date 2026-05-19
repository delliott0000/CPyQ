from __future__ import annotations

from datetime import timedelta
from secrets import token_urlsafe
from typing import TYPE_CHECKING

from .bases import StrIdentifiable
from .codecs import DatetimeCodec, PrimitiveCodec, SerialisableCodec
from .session import Session
from .utils import encode_datetime, now

if TYPE_CHECKING:
    from datetime import datetime
    from typing import Self


class Token(StrIdentifiable):
    codecs = {
        "access": PrimitiveCodec(str),
        "refresh": PrimitiveCodec(str),
        "access_expires": DatetimeCodec(),
        "refresh_expires": DatetimeCodec(),
        "killed_at": DatetimeCodec(optional=True),
        "session": SerialisableCodec(Session),
    }

    access: str
    refresh: str
    access_expires: datetime
    refresh_expires: datetime
    killed_at: datetime | None
    session: Session

    @property
    def killed(self) -> bool:
        return self.killed_at is not None

    @property
    def active(self) -> bool:
        return not self.killed and self.access_expires > now()

    @property
    def expired(self) -> bool:
        return self.killed or self.refresh_expires < now()

    def kill(self) -> bool:
        if self.expired:
            return False

        self.killed_at = now()

        return True

    @staticmethod
    def get_expirations(
        access_expires_in: float, refresh_expires_in: float, /
    ) -> tuple[datetime, datetime]:
        t = now()

        access_expires = t + timedelta(seconds=access_expires_in)
        refresh_expires = t + timedelta(seconds=refresh_expires_in)

        return access_expires, refresh_expires

    def renew(self, *, access_expires_in: float, refresh_expires_in: float) -> bool:
        if self.expired:
            return False

        self.access = token_urlsafe(32)
        self.refresh = token_urlsafe(32)
        self.access_expires, self.refresh_expires = self.get_expirations(
            access_expires_in, refresh_expires_in
        )

        return True

    @classmethod
    def new(
        cls, session: Session, *, access_expires_in: float, refresh_expires_in: float
    ) -> Self:
        access_expires, refresh_expires = cls.get_expirations(
            access_expires_in, refresh_expires_in
        )

        json = {
            "id": token_urlsafe(32),
            "access": token_urlsafe(32),
            "refresh": token_urlsafe(32),
            "access_expires": encode_datetime(access_expires),
            "refresh_expires": encode_datetime(refresh_expires),
            "killed_at": None,
            "session": session.json(),
        }

        return cls(json)
