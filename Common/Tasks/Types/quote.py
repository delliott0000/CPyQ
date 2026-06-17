from ...codecs import SerialisableCodec
from ...quote import Quote
from ..enums import TaskSort
from ..task import Task
from ..tools import register_sort

__all__ = ("ExportQuote",)


@register_sort(TaskSort.ExportQuote)
class ExportQuote(Task):
    codecs = {
        "quote": SerialisableCodec(Quote),
    }

    quote: Quote
