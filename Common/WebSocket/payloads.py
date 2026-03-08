from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from ..bases import JSONSerialisableABC

if TYPE_CHECKING:
    from typing import Any

    Json = dict[str, Any]

__all__ = ("Payload", "payload_factory")


class Payload(JSONSerialisableABC, ABC): ...


def payload_factory(json: Json, /) -> Payload: ...
