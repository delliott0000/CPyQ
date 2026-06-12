from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from .bases import IntIdentifiable
from .codecs import DatetimeCodec, EnumCodec

if TYPE_CHECKING:
    from datetime import datetime
    from typing import Any

    Json = dict[str, Any]

__all__ = (
    "TaskSort",
    "Task",
    "task_sort_to_cls",
    "task_cls_to_sort",
    "parse_received_task",
    "build_task",
)


class TaskSort(StrEnum):
    pass


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


_TASK_MAP: dict[TaskSort, type[Task]] = {}


def task_sort_to_cls(sort: TaskSort, /) -> type[Task]:
    return _TASK_MAP[sort]


_TASK_RMAP: dict[type[Task], TaskSort] = {v: k for k, v in _TASK_MAP.items()}


def task_cls_to_sort(cls: type[Task], /) -> TaskSort:
    return _TASK_RMAP[cls]


def parse_received_task(json: Json, /) -> Task: ...


if TYPE_CHECKING:
    from typing import TypeVar

    TaskT = TypeVar("TaskT", bound=Task)


def build_task(cls: TaskT, json: Json, /) -> TaskT: ...
