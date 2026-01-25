"""
Esempio Componenti - Routes

API routers for the module.
"""
from .categorie import router as categorie_router
from .priorita import router as priorita_router
from .elementi import router as elementi_router

__all__ = [
    "categorie_router",
    "priorita_router",
    "elementi_router",
]
