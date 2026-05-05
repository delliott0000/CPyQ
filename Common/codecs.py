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
    def __init__(self, *types: type, optional: bool = False):
        self.types = types
        self.optional = optional

    def encode(self, value: T, /) -> T:
        return validate(value, *self.types, optional=self.optional)

    def decode(self, value: T, /) -> T:
        return validate(value, *self.types, optional=self.optional)


class DatetimeCodec(Codec):
    def __init__(self, *, optional: bool = False):
        self.optional = optional

    def encode(self, value: datetime | None, /) -> str | None:
        if self.optional and value is None:
            return None
        return encode_datetime(value)

    def decode(self, value: str | None, /) -> datetime | None:
        if self.optional and value is None:
            return None
        return decode_datetime(value)
