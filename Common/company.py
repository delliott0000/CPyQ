from .bases_new import IntIdentifiable
from .codecs import PrimitiveCodec

__all__ = ("Company",)


class Company(IntIdentifiable):
    codecs = {
        "name": PrimitiveCodec(str),
    }

    name: str

    def __str__(self):
        return self.name
