from __future__ import annotations

from typing import TYPE_CHECKING

from ....codecs import SerialisableCodec
from ....Tasks import parse_received_task
from ...enums import WSPeerType
from ..payload import NonEmptyPayload
from ..tools import register_kind

if TYPE_CHECKING:
    from ....Tasks import Task
    from ...response import WSProxy

__all__ = ("TaskAssigned",)


@register_kind(...)
class TaskAssigned(NonEmptyPayload):
    codecs = {
        "task": SerialisableCodec(parse_received_task),
    }

    task: Task

    def valid_context(self, *, receiver: WSProxy) -> bool:
        return (
            not receiver.server
            and receiver.handshake_done
            and receiver.peer_type == WSPeerType.Autopilot
        )
