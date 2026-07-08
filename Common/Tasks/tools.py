from __future__ import annotations

from typing import TYPE_CHECKING

from .enums import TaskSort

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, TypeVar

    from .task import Task

    Json = dict[str, Any]
    TaskT = TypeVar("TaskT", bound=Task)

__all__ = (
    "register_task_sort",
    "task_sort_to_cls",
    "task_cls_to_sort",
    "parse_received_task",
    "build_task",
)


_TASK_MAP: dict[TaskSort, type[Task]] = {}
_TASK_RMAP: dict[type[Task], TaskSort] = {}


def register_task_sort(sort: TaskSort, /) -> Callable[[type[TaskT]], type[TaskT]]:

    def wrapper(cls: type[TaskT], /) -> type[TaskT]:
        _TASK_MAP[sort] = cls
        _TASK_RMAP[cls] = sort

        return cls

    return wrapper


def task_sort_to_cls(sort: TaskSort, /) -> type[Task]:
    return _TASK_MAP[sort]


def task_cls_to_sort(cls: type[Task], /) -> TaskSort:
    return _TASK_RMAP[cls]


def parse_received_task(json: Json, /) -> Task:
    sort = TaskSort(json["sort"])
    cls = task_sort_to_cls(sort)
    return cls(json)


def build_task(cls: type[TaskT], json: Json, /) -> TaskT:
    if "sort" in json:
        raise ValueError('The supplied JSON contains a "sort" field.')

    sort = task_cls_to_sort(cls)
    real_json = {**json, "sort": sort.value}
    return cls(real_json)
