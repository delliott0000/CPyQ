from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from ..bases import IntIdentifiable
from ..codecs import DatetimeCodec, EnumCodec

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


def parse_received_task(json: Json, /) -> Task:
    sort = TaskSort(json["sort"])
    cls = task_sort_to_cls(sort)
    return cls(json)


if TYPE_CHECKING:
    from typing import TypeVar

    TaskT = TypeVar("TaskT", bound=Task)


def build_task(cls: type[TaskT], json: Json, /) -> TaskT:
    if "sort" in json:
        raise ValueError('The supplied JSON contains a "sort" field.')

    sort = task_cls_to_sort(cls)
    real_json = {**json, "sort": sort.value}
    return cls(real_json)
