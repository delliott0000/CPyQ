from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .utils import decode_datetime, encode_datetime, validate

if TYPE_CHECKING:
    from collections.abc import Callable
    from enum import Enum
    from typing import Any

    from .bases_new import Serialisable

    Json = dict[str, Any]
    Primitive = str | int | float | bool
    Container = list | tuple | set | frozenset
    Factory = Callable[[Json], Serialisable]

__all__ = (
    "Codec",
    "EnumCodec",
    "PrimitiveCodec",
    "DatetimeCodec",
    "ContainerCodec",
)


class Codec(ABC):
    @abstractmethod
    def encode(self, value, /):
        pass

    @abstractmethod
    def decode(self, value, /):
        pass


class EnumCodec(Codec):
    def __init__(self, cls: type[Enum], /):
        self.cls = cls

    def encode(self, value, /):
        validate(value, self.cls)
        return value.value

    def decode(self, value, /):
        obj = self.cls(value)
        return obj


class PrimitiveCodec(Codec):
    def __init__(self, *types: type[Primitive], optional: bool = False):
        self.types = types
        self.optional = optional

    def encode(self, value, /):
        return validate(value, *self.types, optional=self.optional)

    def decode(self, value, /):
        return validate(value, *self.types, optional=self.optional)


class DatetimeCodec(Codec):
    def __init__(self, *, optional: bool = False):
        self.optional = optional

    def encode(self, value, /):
        if not self.optional or value is not None:
            return encode_datetime(value)

    def decode(self, value, /):
        if not self.optional or value is not None:
            return decode_datetime(value)


class ContainerCodec(Codec):
    def __init__(self, cls: type[Container], item_codec: Codec, /):
        self.cls = cls
        self.item_codec = item_codec

    def encode(self, value, /):
        validate(value, self.cls)
        return [self.item_codec.encode(item) for item in value]

    def decode(self, value, /):
        validate(value, list)
        return self.cls(self.item_codec.decode(item) for item in value)


class SerialisableCodec(Codec):
    def __init__(self, factory: Factory, /):
        self.factory = factory

    def encode(self, value, /):
        return value.json()

    def decode(self, value, /):
        return self.factory(value)
