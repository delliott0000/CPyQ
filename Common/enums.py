from enum import Enum

__all__ = ("ResourceJSONVersion",)


# fmt: off
class ResourceJSONVersion(Enum):
    metadata = 0
    preview  = 1
    view     = 2
    default  = metadata
# fmt: on
