from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

    Json = dict[str, Any]

__all__ = ("State",)


class State:
    __slots__ = ()

    def to_json(self) -> Json:
        return {}
