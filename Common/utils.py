from __future__ import annotations

from asyncio import get_running_loop
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from functools import partial
from logging import (
    DEBUG,
    ERROR,
    INFO,
    WARNING,
    FileHandler,
    Formatter,
    getLogger,
)
from logging.handlers import QueueHandler, QueueListener
from multiprocessing import Queue
from os import cpu_count, makedirs
from pathlib import Path
from sys import exc_info
from time import time
from typing import TYPE_CHECKING

from bcrypt import checkpw, gensalt, hashpw

from .errors import RatelimitExceeded

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, ParamSpec, Self, TypeVar

    from aiohttp import ClientResponse
    from aiohttp.web import Request

    Json = dict[str, Any]
    P = ParamSpec("P")
    T = TypeVar("T")

__all__ = (
    "now",
    "decode_datetime",
    "encode_datetime",
    "check_password",
    "encrypt_password",
    "check_ratelimit",
    "to_json",
    "log",
    "LoggingContext",
    "create_process_pool",
    "run_in_process_pool",
)


def now() -> datetime:
    return datetime.now().astimezone(timezone.utc)


def decode_datetime(t: str, /) -> datetime:
    return datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%f%z")


def encode_datetime(t: datetime, /) -> str:
    if t.tzinfo is None:
        raise ValueError("Datetime must be timezone-aware.")
    else:
        return t.strftime("%Y-%m-%dT%H:%M:%S.%f%z")


def check_password(password: str, hashed_password: str, /) -> bool:
    return checkpw(password.encode(), hashed_password.encode())


def encrypt_password(password: str, /) -> str:
    return hashpw(password.encode(), gensalt()).decode()


def check_ratelimit(hits: list[float], /, *, limit: int, interval: float) -> list[float]:
    current_time = time()

    recent_hits = [hit for hit in hits if hit + interval > current_time]

    if len(recent_hits) >= limit:
        raise RatelimitExceeded(recent_hits, limit=limit, interval=interval)

    recent_hits.append(current_time)

    return recent_hits


async def to_json(r: Request | ClientResponse, /, *, strict: bool = False) -> Json:
    try:
        data = await r.json()
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict, got {type(data).__name__}.")
        return data
    except Exception as error:
        if strict:
            raise
        log(f"Failed to parse JSON payload - {type(error).__name__}.", WARNING)
        return {}


def log(message: str, level: int = INFO, /) -> None:
    with_traceback = exc_info()[0] is not None and level >= ERROR
    root = getLogger()
    root.log(level, message, exc_info=with_traceback)


class LoggingContext:
    def __init__(self, file: str, level: int = DEBUG, /):
        module = Path(file).parent
        timestamp = now().strftime("%Y-%m-%d_%H-%M-%S")

        self.folder = module.parent / "Logs" / module.name
        self.file = self.folder / f"{timestamp}.txt"
        self.level = level

        self.formatter = Formatter("%(asctime)s - %(levelname)s - %(message)s")

        self.queue: Queue | None = None
        self.listener: QueueListener | None = None

    def __enter__(self) -> Self:
        self.__start__()
        return self

    def __exit__(self, *_) -> None:
        self.__stop__()

    def __start__(self) -> None:
        makedirs(self.folder, exist_ok=True)

        handler = FileHandler(self.file)
        handler.setFormatter(self.formatter)

        self.queue = Queue()
        self.listener = QueueListener(self.queue, handler)
        self.listener.start()

        root = getLogger()
        root.setLevel(self.level)
        root.handlers.clear()
        root.addHandler(QueueHandler(self.queue))

    def __stop__(self) -> None:
        self.listener.stop()
        self.queue.close()
        self.queue.join_thread()


def create_process_pool(*, max_workers: int) -> ProcessPoolExecutor:
    cpus = cpu_count() or 1
    real_max_workers = max(min(cpus - 1, max_workers), 1)
    return ProcessPoolExecutor(max_workers=real_max_workers)


async def run_in_process_pool(
    pool: ProcessPoolExecutor,
    func: Callable[P, T],
    *args: P.args,
    **kwargs: P.kwargs,
) -> T:
    loop = get_running_loop()
    wrapped = partial(func, *args, **kwargs)
    result = await loop.run_in_executor(pool, wrapped)
    return result
