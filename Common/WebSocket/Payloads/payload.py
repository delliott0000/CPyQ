from __future__ import annotations

from typing import TYPE_CHECKING

from ...bases import Serialisable
from ...codecs import EnumCodec
from .enums import PayloadKind

if TYPE_CHECKING:
    from ..response import WSProxy

__all__ = ("Payload", "NonEmptyPayload", "EmptyPayload", "EMPTY_PAYLOAD")


class Payload(Serialisable):
    def valid_context(self, *, receiver: WSProxy) -> bool:
        raise NotImplementedError


class NonEmptyPayload(Payload):
    codecs = {
        "kind": EnumCodec(PayloadKind),
    }

    kind: PayloadKind


class EmptyPayload(Payload):
    def valid_context(self, *, receiver: WSProxy) -> bool:
        return receiver.handshake_done


EMPTY_PAYLOAD = EmptyPayload({})
