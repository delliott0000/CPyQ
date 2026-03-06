from __future__ import annotations

from typing import TYPE_CHECKING

from .bases import JSONSerialisableABC

if TYPE_CHECKING:
    from typing import Any

    Json = dict[str, Any]

__all__ = ("State",)


class State(JSONSerialisableABC):
    __slots__ = ()

    def json(self) -> Json:
        return {}
