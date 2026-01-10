"""
Anagrafica Italiana Module

This module provides Italian-specific registry functionality for managing
persons and companies according to Italian regulations.
"""
# Import models to ensure they're available early (before routes are loaded)
from . import models
from .routes import (
    soggetti_router,
    soggetti_v2_router,
    domini_router,
    ruoli_azienda_router,
    ruoli_azienda_tipi_router,
    documenti_router
)
from .__manifest__ import manifest

# Routers provided by this module
ROUTERS = [
    soggetti_router,
    soggetti_v2_router,
    domini_router,
    ruoli_azienda_router,
    ruoli_azienda_tipi_router,
    documenti_router
]

# Menu items da registrare con la platform (dalla manifest)
MENU_ITEMS = manifest.get("menu_items", [])

# Widget da registrare con la platform (dalla manifest)
WIDGETS = manifest.get("widgets", [])

# Legacy export for backward compatibility
router = soggetti_router

__all__ = ["router", "ROUTERS", "manifest", "models", "MENU_ITEMS", "WIDGETS"]


def register_module(app):
    """
    Called by the module loader to register this module with the application.

    Args:
        app: The FastAPI application instance
    """
    print("[Anagrafica Italiana Module] Registering module...")
    print("[Anagrafica Italiana Module] Providing Italian registry functionality")
    print("[Anagrafica Italiana Module] Registration complete!")
