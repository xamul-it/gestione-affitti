"""
Schemas for Italian Registry (Anagrafica Italiana) module.
"""
from .soggetto_anagrafico import (
    TipoSoggettoEnum,
    SoggettoAnagraficoBase,
    SoggettoAnagraficoCreate,
    SoggettoAnagraficoUpdate,
    SoggettoAnagraficoResponse,
    CompleteSoggettoFromDocument,
)
from .document_parsing import CompleteDocumentoParsing
from .similarity_matching import FindSimilarRequest

__all__ = [
    "TipoSoggettoEnum",
    "SoggettoAnagraficoBase",
    "SoggettoAnagraficoCreate",
    "SoggettoAnagraficoUpdate",
    "SoggettoAnagraficoResponse",
    "CompleteSoggettoFromDocument",
    "CompleteDocumentoParsing",
    "FindSimilarRequest",
]
