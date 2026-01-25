"""
Routes for immobili module
"""
from .categorie_catastali import router as categorie_catastali_router
from .terreni import router as terreni_router
from .tipologie_terreno import router as tipologie_terreno_router

__all__ = ["categorie_catastali_router", "terreni_router", "tipologie_terreno_router"]
