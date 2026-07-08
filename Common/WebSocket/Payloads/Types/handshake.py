from __future__ import annotations

from typing import TYPE_CHECKING

from ....codecs import PrimitiveCodec
from ..enums import PayloadKind
from ..payload import NonEmptyPayload
from ..tools import register_payload_kind

if TYPE_CHECKING:
    from ...response import WSProxy


class Handshake(NonEmptyPayload):
    codecs = {
        "ack_timeout": PrimitiveCodec(float),
    }

    ack_timeout: float

    def valid_context(self, *, receiver: WSProxy) -> bool:
        return (
            not receiver.server and not receiver.handshake_set and receiver.is_handshake(self)
        )


@register_payload_kind(PayloadKind.UserHandshake)
class UserHandshake(Handshake):
    codecs = {}


@register_payload_kind(PayloadKind.AutopilotHandshake)
class AutopilotHandshake(Handshake):
    codecs = {}
