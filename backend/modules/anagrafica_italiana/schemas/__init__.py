"""
Schemas for Italian Registry (Anagrafica Italiana) module.
"""
from .soggetto_anagrafico import (
    TipoSoggettoEnum,
    SoggettoAnagraficoBase,
    SoggettoAnagraficoCreate,
    SoggettoAnagraficoUpdate,
    SoggettoAnagraficoResponse,
)

__all__ = [
    "TipoSoggettoEnum",
    "SoggettoAnagraficoBase",
    "SoggettoAnagraficoCreate",
    "SoggettoAnagraficoUpdate",
    "SoggettoAnagraficoResponse",
]
