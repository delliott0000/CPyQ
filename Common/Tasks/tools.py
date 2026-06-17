from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import TypeVar

    from .enums import TaskSort
    from .task import Task

    TaskT = TypeVar("TaskT", bound=Task)

__all__ = ("register_sort", "task_sort_to_cls", "task_cls_to_sort")


_TASK_MAP: dict[TaskSort, type[Task]] = {}
_TASK_RMAP: dict[type[Task], TaskSort] = {}


def register_sort(sort: TaskSort, /) -> Callable[[type[TaskT]], type[TaskT]]:

    def wrapper(cls: type[TaskT], /) -> type[TaskT]:
        _TASK_MAP[sort] = cls
        _TASK_RMAP[cls] = sort

        return cls

    return wrapper


def task_sort_to_cls(sort: TaskSort, /) -> type[Task]:
    return _TASK_MAP[sort]


def task_cls_to_sort(cls: type[Task], /) -> TaskSort:
    return _TASK_RMAP[cls]
