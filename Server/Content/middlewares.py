from __future__ import annotations

from logging import ERROR
from typing import TYPE_CHECKING

from aiohttp.web import HTTPException, json_response, middleware
from multidict import CIMultiDict

from Common import log

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine
    from typing import Any

    from aiohttp.web import Request, Response

    Handler = Callable[[Request], Coroutine[Any, Any, Response]]

__all__ = ("middlewares",)


@middleware
async def json_wrapper(request: Request, handler: Handler) -> Response:
    try:
        return await handler(request)

    except HTTPException as error:
        headers = CIMultiDict(error.headers or {})
        headers.pop("Content-Type", None)

        payload = {"message": error.reason}
        payload.update(getattr(error, "_extra_data", {}))

        return json_response(payload, status=error.status, headers=headers)

    except Exception as error:
        log(f"An error occurred whilst processing a request.", ERROR, error=error)
        return json_response({"message": "Internal server error"}, status=500)


middlewares = (json_wrapper,)
