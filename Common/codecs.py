from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .utils import decode_datetime, encode_datetime, validate

if TYPE_CHECKING:
    from datetime import datetime
    from typing import Any, TypeVar

    T = TypeVar("T")

__all__ = (
    "Codec",
    "JSONCodec",
    "EnumCodec",
    "TypedCodec",
    "DatetimeCodec",
    "float_codec",
    "int_codec",
    "str_codec",
    "dt_codec",
)


class Codec(ABC):
    @abstractmethod
    def encode(self, value: Any, /) -> Any:
        pass

    @abstractmethod
    def decode(self, value: Any, /) -> Any:
        pass


class JSONCodec(Codec):
    def encode(self, value: ..., /) -> ...: ...

    def decode(self, value: ..., /) -> ...: ...


class EnumCodec(Codec):
    def encode(self, value: ..., /) -> ...: ...

    def decode(self, value: ..., /) -> ...: ...


class TypedCodec(Codec):
    def __init__(self, expected_types: type | tuple[type, ...], /, *, optional: bool = False):
        self.expected_types = expected_types
        self.optional = optional

    def encode(self, value: T, /) -> T:
        return validate(self.expected_types, value, optional=self.optional)

    def decode(self, value: T, /) -> T:
        return validate(self.expected_types, value, optional=self.optional)


class DatetimeCodec(Codec):
    def encode(self, value: datetime, /) -> str:
        return encode_datetime(value)

    def decode(self, value: str, /) -> datetime:
        return decode_datetime(value)


float_codec = TypedCodec(float)
int_codec = TypedCodec(int)
str_codec = TypedCodec(str)
dt_codec = DatetimeCodec()
