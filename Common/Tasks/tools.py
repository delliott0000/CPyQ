from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from .enums import TaskSort

__all__ = ("register_sort",)


_TASK_MAP: dict[TaskSort, ...] = {}
_TASK_RMAP: dict[..., TaskSort] = {}


def register_sort(sort: TaskSort, /) -> Callable[[...], ...]: ...
