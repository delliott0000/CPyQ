from dataclasses import dataclass
from enum import Enum, IntEnum, StrEnum

__all__ = (
    "CustomWSCloseCode",
    "CustomWSMessageType",
    "WSEventStatus",
    "PayloadKind",
    "WSPeerRole",
    "WSPeerType",
    "WSPeerScope",
    "HandshakePhase",
)


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


class WSPeerRole(Enum):
    Server = 0
    Client = 1


class WSPeerType(Enum):
    User      = 0
    Autopilot = 1


# Not an enumeration, but defining this here is convenient
@dataclass(kw_only=True, frozen=True, slots=True)
class WSPeerScope:
    role: WSPeerRole
    type: WSPeerType


class HandshakePhase(Enum):
    NotStarted = 0
    InProgress = 1
    Done       = 2
# fmt: on
