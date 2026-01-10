"""
Pydantic schemas for the Immobili module.
"""
from .categoria_catastale import (
    CategoriaCatastaleBase,
    CategoriaCatastaleCreate,
    CategoriaCatastaleUpdate,
    CategoriaCatastale,
)
from .tipologia_terreno import (
    TipologiaTerrenoBase,
    TipologiaTerrenoCreate,
    TipologiaTerrenoUpdate,
    TipologiaTerrenoResponse,
    TipologiaTerrenoSimple,
)
from .terreno import (
    TerrenoBase,
    TerrenoCreate,
    TerrenoUpdate,
    TerrenoResponse,
)

__all__ = [
    # Categoria Catastale
    "CategoriaCatastaleBase",
    "CategoriaCatastaleCreate",
    "CategoriaCatastaleUpdate",
    "CategoriaCatastale",
    # Tipologia Terreno
    "TipologiaTerrenoBase",
    "TipologiaTerrenoCreate",
    "TipologiaTerrenoUpdate",
    "TipologiaTerrenoResponse",
    "TipologiaTerrenoSimple",
    # Terreno
    "TerrenoBase",
    "TerrenoCreate",
    "TerrenoUpdate",
    "TerrenoResponse",
]
