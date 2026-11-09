"""Entry point: PDF bytes -> VisuraParsed (format auto-detected)."""
from .models import VisuraFormatError, VisuraParsed
from .parser_analitica import parse_analitica
from .parser_immobile import parse_immobile
from .parser_sintetica import parse_sintetica
from .text import UNSUPPORTED_MSG, pdf_to_text

# Checked in order: more specific titles first.
_LAYOUTS = (
    ("Visura attuale sintetica per soggetto", lambda t: parse_sintetica(t)),
    ("Visura attuale per soggetto", lambda t: parse_analitica(t)),
    ("Visura attuale per immobile", lambda t: parse_analitica(t, per_immobile=True)),
    ("Visura per immobile", lambda t: parse_immobile(t)),
)


def parse_visura(pdf_bytes: bytes) -> VisuraParsed:
    text = pdf_to_text(pdf_bytes)
    for title, parse in _LAYOUTS:
        if title in text:
            return parse(text)
    raise VisuraFormatError(UNSUPPORTED_MSG)
