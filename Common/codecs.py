from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .utils import decode_datetime, encode_datetime, validate

if TYPE_CHECKING:
    from enum import Enum

__all__ = (
    "Codec",
    "EnumCodec",
    "TypedCodec",
    "DatetimeCodec",
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


class TypedCodec(Codec):
    def __init__(self, *types: type, optional: bool = False):
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
