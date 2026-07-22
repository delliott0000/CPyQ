from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine
    from typing import Any

    from Common import TaskSort

    from .postgresql import PostgreSQLClient

    Json = dict[str, Any]
    ReaderCoro = Coroutine[Any, Any, Json]
    ReaderFunc = Callable[[PostgreSQLClient, Json], ReaderCoro]
    ReaderDeco = Callable[[ReaderFunc], ReaderFunc]

__all__ = ("task_reader", "get_task_reader")


_TASK_READERS: dict[TaskSort, ReaderFunc] = {}


def task_reader(sort: TaskSort, /) -> ReaderDeco:

    def wrapper(func: ReaderFunc, /) -> ReaderFunc:
        _TASK_READERS[sort] = func

        return func

    return wrapper


def get_task_reader(sort: TaskSort, /) -> ReaderFunc:
    return _TASK_READERS[sort]
