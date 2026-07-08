from __future__ import annotations

from typing import TYPE_CHECKING

from ....codecs import PrimitiveCodec
from ...enums import WSPeerType
from ..payload import NonEmptyPayload

if TYPE_CHECKING:
    from ...response import WSProxy

__all__ = ("TaskDone",)


class TaskDone(NonEmptyPayload):
    codes = {
        "task_id": PrimitiveCodec(int),
    }

    task_id: int

    def valid_context(self, *, receiver: WSProxy) -> bool:
        return (
            receiver.server
            and receiver.handshake_done
            and receiver.peer_type == WSPeerType.Autopilot
        )
