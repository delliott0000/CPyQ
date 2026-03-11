from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from ..bases import JSONSerialisableABC

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, ClassVar

    Json = dict[str, Any]
    Validator = Callable[[Any], Any]

__all__ = ("Payload", "EmptyPayload", "payload_factory")


class Payload(JSONSerialisableABC, ABC):
    VALIDATORS: ClassVar[dict[str, Validator] | None] = None

    def __init__(self, json: Json, /):
        if type(self) is Payload:
            # Leave this here for safety; ABC will raise TypeError, but don't rely on that
            raise NotImplementedError(
                "Payload is an abstract base class and cannot be instantiated directly."
            )
        elif self.VALIDATORS is None:
            raise RuntimeError("Payload subclasses must each define their own validators.")

        # This may be made recursive in the future to handle nested structures
        for key, validator in self.VALIDATORS.items():
            setattr(self, key, validator(json[key]))


class EmptyPayload(Payload):
    __instance__: EmptyPayload | None = None

    def __new__(cls, _: Json, /):
        if cls.__instance__ is None:
            cls.__instance__ = super().__new__(cls)
        return cls.__instance__

    def __init__(self, _: Json, /):  # noqa
        pass

    def json(self) -> Json:
        return {}


def payload_factory(json: Json, /) -> Payload:
    if not json:
        cls = EmptyPayload
    else:
        cls = ...

    return cls(json)
