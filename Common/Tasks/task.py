from __future__ import annotations

from typing import TYPE_CHECKING

from ..bases import IntIdentifiable
from ..codecs import DatetimeCodec, EnumCodec
from .enums import TaskSort

if TYPE_CHECKING:
    from datetime import datetime

__all__ = ("Task",)


class Task(IntIdentifiable):
    codecs = {
        "sort": EnumCodec(TaskSort),
        "created_at": DatetimeCodec(),
        "completed_at": DatetimeCodec(optional=True),
    }

    sort: TaskSort
    created_at: datetime
    completed_at: datetime | None

    @property
    def pending(self) -> bool:
        return self.completed_at is None
