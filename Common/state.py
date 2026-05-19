from __future__ import annotations

from typing import TYPE_CHECKING

from .bases import Serialisable

if TYPE_CHECKING:
    from typing import Self

__all__ = ("State",)


class State(Serialisable):
    @classmethod
    def new(cls) -> Self:
        json = {}
        return cls(json)
