from enum import StrEnum

__all__ = ("PayloadKind",)


# fmt: off
class PayloadKind(StrEnum):
    UserHandshake      = "user_handshake"
    AutopilotHandshake = "autopilot_handshake"
    TaskAssigned       = "task_assigned"
    TaskDone           = "task_done"
# fmt: on
