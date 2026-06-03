from __future__ import annotations

from typing import TYPE_CHECKING

from .bases import IntIdentifiable
from .codecs import DatetimeCodec

if TYPE_CHECKING:
    from datetime import datetime

__all__ = ("Task",)


class Task(IntIdentifiable):
    codecs = {
        "created_at": DatetimeCodec(),
        "completed_at": DatetimeCodec(optional=True),
    }

    created_at: datetime
    completed_at: datetime | None

    @property
    def complete(self) -> bool:
        return self.completed_at is not None
