from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

    Json = dict[str, Any]

__all__ = (
    "ComparesIDABC",
    "ComparesIDMixin",
    "ComparesIDFormattedABC",
    "ComparesIDFormattedMixin",
    "JSONSerialisableABC",
)


# This *might* be overengineered.


class ComparesIDABC(ABC):
    __slots__ = ()

    @property
    @abstractmethod
    def id(self) -> Any:
        pass


class ComparesIDMixin:
    __slots__ = ()

    id: Any  # Provided by ComparesIDABC

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, ComparesIDMixin):
            return self.id == other.id
        return NotImplemented


class ComparesIDFormattedABC(ComparesIDABC, ABC):
    __slots__ = ()

    @property
    @abstractmethod
    def formatted_id(self) -> str:
        pass


class ComparesIDFormattedMixin(ComparesIDMixin):
    __slots__ = ()

    formatted_id: str  # Provided by ComparesIDFormattedABC

    def __str__(self):
        return self.formatted_id


class JSONSerialisableABC(ABC):
    __slots__ = ()

    @abstractmethod
    def json(self) -> Json:
        pass
