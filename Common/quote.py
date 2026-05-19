from .bases import Formattable, IntIdentifiable

__all__ = ("QuoteMetadata", "QuotePreview", "QuoteView", "Quote")


class QuoteMetadata(Formattable, IntIdentifiable):
    prefix = "SQ"
    padding = 6

    codecs = {}


class QuotePreview(QuoteMetadata):
    codecs = {}


class QuoteView(QuotePreview):
    codecs = {}


class Quote(QuoteView):
    metadata_type = QuoteMetadata
    preview_type = QuotePreview
    view_type = QuoteView
