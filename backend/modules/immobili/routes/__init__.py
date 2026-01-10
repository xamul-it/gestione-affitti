"""
Routes for immobili module
"""
from .categorie_catastali import router as categorie_catastali_router
from .terreni import router as terreni_router

__all__ = ["categorie_catastali_router", "terreni_router"]
