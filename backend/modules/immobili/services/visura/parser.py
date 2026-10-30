"""Entry point: PDF bytes -> VisuraParsed (format auto-detected)."""
from .models import FormatoVisura, VisuraParsed
from .parser_analitica import parse_analitica
from .parser_sintetica import parse_sintetica
from .text import detect_formato, pdf_to_text


def parse_visura(pdf_bytes: bytes) -> VisuraParsed:
    text = pdf_to_text(pdf_bytes)
    formato = detect_formato(text)
    if formato == FormatoVisura.SINTETICA:
        return parse_sintetica(text)
    return parse_analitica(text)
