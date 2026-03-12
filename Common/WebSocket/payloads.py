from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from ..bases import JSONSerialisableABC
from ..utils import validate

if TYPE_CHECKING:
    from typing import Any

    Json = dict[str, Any]

__all__ = ("Payload", "payload_factory")


class Payload(JSONSerialisableABC, ABC):
    def __init__(self, json: Json, /): ...

    def json(self) -> Json: ...


def payload_factory(json: Json, /) -> Payload:
    validate(dict, json)

    if not json:
        return ...
    else:
        return ...
