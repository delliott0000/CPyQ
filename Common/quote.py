from .bases import Formattable, IntIdentifiable

__all__ = ("QuoteMetadata", "QuotePreview", "QuoteView")


class QuoteMetadata(Formattable, IntIdentifiable):
    prefix = "SQ"
    padding = 6


class QuotePreview(QuoteMetadata): ...


class QuoteView(QuotePreview): ...
