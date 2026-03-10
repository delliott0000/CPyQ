from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from ..bases import JSONSerialisableABC

if TYPE_CHECKING:
    from typing import Any

    Json = dict[str, Any]

__all__ = ("Payload", "EmptyPayload", "payload_factory")


class Payload(JSONSerialisableABC, ABC): ...


class EmptyPayload(Payload):
    __instance__ = None

    def __new__(cls, *args: Any, **kwargs: Any):
        if cls.__instance__ is None:
            cls.__instance__ = super().__new__(cls, *args, **kwargs)
        return cls.__instance__

    def json(self) -> Json:
        return {}


def payload_factory(json: Json, /) -> Payload:
    if not json:
        return EmptyPayload()

    ...
