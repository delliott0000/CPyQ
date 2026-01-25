from __future__ import annotations

from asyncio import get_running_loop
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from functools import partial
from logging import DEBUG, ERROR, INFO, WARNING, basicConfig, getLogger
from os import cpu_count, makedirs
from pathlib import Path
from sys import exc_info
from time import time
from typing import TYPE_CHECKING

from bcrypt import checkpw, gensalt, hashpw

from .errors import RatelimitExceeded

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, ParamSpec, TypeVar

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
    "setup_logging",
    "check_ratelimit",
    "log",
    "to_json",
    "create_process_pool",
    "run_in_process_pool",
)


_logger = getLogger()


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


def setup_logging(file: str, level: int = DEBUG, /) -> None:
    current_module = Path(file).parent
    log_destination = current_module.parent / "Logs" / current_module.name

    timestamp = now().strftime("%Y-%m-%d_%H-%M-%S")

    makedirs(log_destination, exist_ok=True)

    basicConfig(
        filename=log_destination / f"{timestamp}.txt",
        filemode="w",
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def check_ratelimit(hits: list[float], /, *, limit: int, interval: float) -> list[float]:
    current_time = time()

    recent_hits = [hit for hit in hits if hit + interval > current_time]

    if len(recent_hits) >= limit:
        raise RatelimitExceeded(recent_hits, limit=limit, interval=interval)

    recent_hits.append(current_time)

    return recent_hits


def log(message: str, level: int = INFO, /) -> None:
    with_traceback = exc_info()[0] is not None and level >= ERROR
    _logger.log(level, message, exc_info=with_traceback)


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
