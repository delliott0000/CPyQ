from enum import IntEnum, StrEnum

__all__ = ("CustomWSCloseCode", "CustomWSMessageType", "WSEventStatus", "PayloadKind")


# fmt: off
class CustomWSCloseCode(IntEnum):
    TokenExpired      = 4000
    InvalidFrameType  = 4001
    InvalidJSON       = 4002
    MissingField      = 4003
    InvalidType       = 4004
    InvalidValue      = 4005
    DuplicateEventID  = 4006
    AckTimeout        = 4007
    UnknownEvent      = 4008
    FatalEvent        = 4009
    BadPayloadContext = 4010
    InternalError     = 4999


class CustomWSMessageType(StrEnum):
    Event = "event"
    Ack   = "ack"


class WSEventStatus(StrEnum):
    Normal = "normal"
    Error  = "error"
    Fatal  = "fatal"


class PayloadKind(StrEnum):
    UserHandshake      = "user_handshake"
    AutopilotHandshake = "autopilot_handshake"
# fmt: on
