from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from ..bases import JSONSerialisableABC

if TYPE_CHECKING:
    from typing import Any, ClassVar

    Json = dict[str, Any]

__all__ = ("Payload", "payload_factory")


class Payload(JSONSerialisableABC, ABC):
    TYPE_MAP: ClassVar[Json | None] = None

    def __init__(self, json: Json, /):
        if type(self) is Payload:
            raise NotImplementedError(
                "Payload is an abstract base class and cannot be instantiated directly."
            )
        elif self.TYPE_MAP is None:
            raise RuntimeError("Payload subclasses must define a type map.")

        ...


def payload_factory(json: Json, /) -> Payload: ...
