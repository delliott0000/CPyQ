from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from ..bases import JSONSerialisableABC
from ..codecs import float_codec
from ..utils import validate
from .enums import PayloadKind

if TYPE_CHECKING:
    from typing import Any, ClassVar

    from ..codecs import Codec

    Json = dict[str, Any]

__all__ = ("Payload", "EmptyPayload", "EMPTY_PAYLOAD", "payload_kind", "payload_factory")


class Payload(JSONSerialisableABC, ABC):
    CODECS: ClassVar[dict[str, Codec] | None] = None

    def __init__(self, json: Json, /):
        if type(self) is Payload:
            raise NotImplementedError(
                "Payload is an abstract base class and must not be instantiated directly."
            )
        elif self.CODECS is None:
            raise RuntimeError("Payload subclasses must each define their own codecs.")

        # Already validated by the factory
        self._kind = json["kind"]

        for key, codec in self.CODECS.items():
            setattr(self, key, codec.decode(json[key]))

    def json(self) -> Json:
        return {"kind": self._kind} | {
            key: codec.encode(getattr(self, key)) for key, codec in self.CODECS.items()
        }


class EmptyPayload(Payload):
    def __init__(self):  # noqa
        pass

    def json(self) -> Json:
        return {}


class Handshake(Payload, ABC):
    CODECS = {
        "ack_timeout": float_codec,
    }


EMPTY_PAYLOAD = EmptyPayload()


_MAPPING = {}


def payload_kind(kind: PayloadKind, /) -> type[Payload]:
    return _MAPPING[kind]


def payload_factory(json: Json, /) -> Payload:
    validate(dict, json)

    if not json:
        return EMPTY_PAYLOAD

    else:
        kind = PayloadKind(json["kind"])
        cls = payload_kind(kind)
        return cls(json)
