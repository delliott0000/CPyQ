from __future__ import annotations

from asyncio import get_running_loop
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from functools import partial
from logging import (
    DEBUG,
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
from signal import SIGINT, SIGTERM, signal
from time import time
from typing import TYPE_CHECKING

from bcrypt import checkpw, gensalt, hashpw

from .errors import RatelimitException
from .format import ENCODE_DATETIME_FORMAT, FILE_DATE_FORMAT, LOGGING_FORMAT

if TYPE_CHECKING:
    from asyncio import Future
    from collections.abc import Callable
    from typing import Any, ParamSpec, Self, TypeVar

    from aiohttp import ClientResponse
    from aiohttp.web import Request

    Json = dict[str, Any]
    P = ParamSpec("P")
    T = TypeVar("T")

__all__ = (
    "root_dir",
    "now",
    "decode_datetime",
    "encode_datetime",
    "check_password",
    "encrypt_password",
    "check_ratelimit",
    "to_json",
    "LoggingContext",
    "log",
    "CustomProcessPoolExecutor",
    "create_process_pool",
    "initialize_process",
)


def root_dir() -> Path:
    import sys

    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).resolve().parent.parent


def now() -> datetime:
    return datetime.now().astimezone(timezone.utc)


def decode_datetime(t: str, /) -> datetime:
    return datetime.strptime(t, ENCODE_DATETIME_FORMAT)


def encode_datetime(t: datetime, /) -> str:
    if t.tzinfo is None:
        raise ValueError("Datetime must be timezone-aware.")
    else:
        return t.strftime(ENCODE_DATETIME_FORMAT)


def check_password(password: str, hashed_password: str, /) -> bool:
    return checkpw(password.encode(), hashed_password.encode())


def encrypt_password(password: str, /) -> str:
    return hashpw(password.encode(), gensalt()).decode()


def check_ratelimit(hits: list[float], /, *, limit: int, interval: float) -> None:
    t = time()
    cutoff = t - interval

    hits[:] = [hit for hit in hits if hit > cutoff]

    if len(hits) >= limit:
        raise RatelimitException(hits, limit=limit, interval=interval)

    hits.append(t)


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


def _setup_handler(level: int, queue: Queue, /) -> None:
    root = getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(QueueHandler(queue))


class LoggingContext:
    def __init__(self, module: str, level: int = DEBUG, /):
        self.folder = root_dir() / "Logs" / module
        self.file = self.folder / f"{now().strftime(FILE_DATE_FORMAT)}.txt"
        self.level = level

        self.formatter = Formatter(LOGGING_FORMAT)

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

        _setup_handler(self.level, self.queue)

    def __stop__(self) -> None:
        self.listener.stop()
        self.queue.close()
        self.queue.join_thread()


def log(message: str, level: int = INFO, /, *, error: BaseException | None = None) -> None:
    root = getLogger()
    root.log(level, message, exc_info=error)


class CustomProcessPoolExecutor(ProcessPoolExecutor):
    def submit_async(
        self,
        func: Callable[P, T],
        /,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> Future[T]:
        loop = get_running_loop()
        wrapped = partial(func, *args, **kwargs)
        return loop.run_in_executor(self, wrapped)


def create_process_pool(*, max_workers: int, **kwargs: Any) -> CustomProcessPoolExecutor:
    cpus = cpu_count() or 1
    real_max_workers = max(min(cpus - 1, max_workers), 1)
    return CustomProcessPoolExecutor(max_workers=real_max_workers, **kwargs)


def _signal_interrupt(code: int, /, *_) -> None:
    raise SystemExit(code)


def initialize_process(level: int, queue: Queue, /) -> None:
    _setup_handler(level, queue)
    signal(SIGINT, partial(_signal_interrupt, 130))
    signal(SIGTERM, partial(_signal_interrupt, 143))
    log("Child process initialized.")
