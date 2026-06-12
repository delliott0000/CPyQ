from __future__ import annotations

from typing import TYPE_CHECKING

from .bases import IntIdentifiable
from .codecs import DatetimeCodec

if TYPE_CHECKING:
    from datetime import datetime
    from typing import Any

    Json = dict[str, Any]

__all__ = ("Task", "parse_received_task", "task_factory")


class Task(IntIdentifiable):
    codecs = {
        "created_at": DatetimeCodec(),
        "completed_at": DatetimeCodec(optional=True),
    }

    created_at: datetime
    completed_at: datetime | None

    @property
    def pending(self) -> bool:
        return self.completed_at is None


if TYPE_CHECKING:
    from typing import TypeVar

    TaskT = TypeVar("TaskT", bound=Task)


def parse_received_task(json: Json, /) -> Task: ...


def task_factory(cls: TaskT, json: Json, /) -> TaskT: ...
