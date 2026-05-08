from __future__ import annotations

from typing import TYPE_CHECKING

from .codecs import PrimitiveCodec

if TYPE_CHECKING:
    from typing import Any, ClassVar, TypeVar

    from .codecs import Codec

    Json = dict[str, Any]
    T = TypeVar("T")

__all__ = (
    "SerialisableMeta",
    "Serialisable",
    "Identifiable",
    "StrIdentifiable",
    "IntIdentifiable",
    "Formattable",
)


class SerialisableMeta(type):
    def __new__(
        cls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ):
        all_codecs = {}

        # Gather inherited codecs from base classes
        # Iterating in reverse order is important
        # Bases that are higher up in the MRO will overwrite bases that are lower down
        for base in reversed(bases):
            inherited_codecs = getattr(base, "codecs", {})
            all_codecs.update(inherited_codecs)

        # Add codecs from the current class
        current_codecs = namespace.get("codecs", {})
        all_codecs.update(current_codecs)

        # Update the current class's codecs to include the inherited codecs
        namespace["codecs"] = all_codecs

        # Compute the current class's slots
        # Include the current class's codecs and any explicitly-defined slots
        current_slots = tuple(current_codecs.keys())
        extra_slots = namespace.get("__slots__", ())

        # Normalise the '__slots__ = "..."' special case
        if isinstance(extra_slots, str):
            extra_slots = (extra_slots,)
        else:
            extra_slots = tuple(extra_slots)

        # De-duplicate the slots (and maintain order)
        all_slots = tuple(dict.fromkeys(current_slots + extra_slots))
        namespace["__slots__"] = all_slots

        return super().__new__(cls, name, bases, namespace, **kwargs)


class Serialisable(metaclass=SerialisableMeta):
    codecs: ClassVar[dict[str, Codec]] = {}

    def __init__(self, json: Json, /):
        cls = type(self)

        if cls is Serialisable:
            raise RuntimeError(f"{cls.__name__} must not be directly instantiated.")

        for key, codec in cls.codecs.items():
            setattr(self, key, codec.decode(json[key]))

    def json(self) -> Json:
        # fmt: off
        return {
            key: codec.encode(getattr(self, key))
            for key, codec in type(self).codecs.items()
        }
        # fmt: on

    def decompose(self, base: type[T], /) -> T:
        cls = type(self)

        if not issubclass(cls, base):
            raise ValueError(f"{base.__name__} is not a base class of {cls.__name__}.")
        elif not issubclass(base, Serialisable):
            raise ValueError(f"{base.__name__} is not a subclass of Serialisable.")

        return base(self.json())


class Identifiable(Serialisable):
    codecs = {
        "id": PrimitiveCodec(object),
    }

    id: object

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, Identifiable):
            return self.id == other.id
        return NotImplemented


class StrIdentifiable(Identifiable):
    codecs = {
        "id": PrimitiveCodec(str),
    }

    id: str


class IntIdentifiable(Identifiable):
    codecs = {
        "id": PrimitiveCodec(int),
    }

    id: int


class Formattable(Identifiable):
    prefix: ClassVar[str] = ""
    padding: ClassVar[int] = 0

    @property
    def formatted_id(self) -> str:
        if isinstance(self.id, int):
            padded_id = f"{self.id:0{self.padding}d}"
        else:
            padded_id = str(self.id)

        return self.prefix + padded_id

    def __str__(self):
        return self.formatted_id
