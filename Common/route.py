from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING
from urllib.parse import quote

if TYPE_CHECKING:
    from typing import ClassVar

    from .config import APIConfig

__all__ = ("build_base", "setup_routes", "Route", "HTTPRoute", "WebSocketRoute")


def build_base(protocol: str, domain: str, use_secure: bool, /) -> str:
    return f"{protocol}{'s' if use_secure else ''}://{domain}"


def setup_routes(config: APIConfig, /) -> None:
    use_secure = config.secure and not config.local

    if config.local:
        resolved_domain = f"{config.host}:{config.port}"
    else:
        resolved_domain = config.domain

    HTTPRoute.BASE = build_base("http", resolved_domain, use_secure)
    WebSocketRoute.BASE = build_base("ws", resolved_domain, use_secure)


class Route(ABC):
    BASE: ClassVar[str] = ""

    def __init__(self, path: str, /, **kwargs: str):
        if type(self) is Route:
            raise NotImplementedError(
                "Route is an abstract base class and cannot be instantiated directly."
            )
        elif self.BASE == "":
            raise RuntimeError(
                "Route instances must have a base. Did you forget to call setup_routes(...)?"
            )

        self.__path: str = path
        self.__kwargs: dict[str, str] = {k: quote(v, safe="") for k, v in kwargs.items()}

    def __str__(self):
        return self.url

    @property
    def url(self) -> str:
        return self.BASE + self.__path.format(**self.__kwargs)


class HTTPRoute(Route):
    pass


class WebSocketRoute(Route):
    pass
