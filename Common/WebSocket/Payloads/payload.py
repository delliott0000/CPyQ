from __future__ import annotations

from typing import TYPE_CHECKING

from ...bases import Serialisable

if TYPE_CHECKING:
    from ..response import WSProxy

__all__ = ("Payload",)


class Payload(Serialisable):
    def valid_context(self, *, receiver: WSProxy) -> bool:
        raise NotImplementedError
