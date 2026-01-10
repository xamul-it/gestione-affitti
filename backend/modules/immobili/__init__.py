"""
Immobili Module - Real Estate Property Management

Manages properties, condominiums, owners, and cadastral data.
"""
# Import models to ensure they're available early (before routes are loaded)
from . import models
from .routes import categorie_catastali_router, terreni_router
from .__manifest__ import manifest

# Routers provided by this module
ROUTERS = [categorie_catastali_router, terreni_router]

# Menu items da registrare con la platform
MENU_ITEMS = [
    {
        "id": "immobili.unita",
        "label": "Unità Immobiliari",
        "path": "/unita-immobiliari",
        "icon": "building",
        "order_index": 10,
        "required_permission": "immobile.view"
    },
    {
        "id": "immobili.proprietari",
        "label": "Proprietari",
        "path": "/proprietari",
        "icon": "user",
        "order_index": 20,
        "required_permission": "proprietario.view"
    },
    {
        "id": "immobili.condomini",
        "label": "Condomini",
        "path": "/condomini",
        "icon": "building-2",
        "order_index": 30,
        "required_permission": "condominio.view"
    },
    {
        "id": "immobili.certificati",
        "label": "Certificati Energetici",
        "path": "/certificati-energetici",
        "icon": "zap",
        "order_index": 40,
        "required_permission": "certificato_energetico.view"
    },
    {
        "id": "immobili.terreni",
        "label": "Terreni",
        "path": "/terreni",
        "icon": "leaf",
        "order_index": 15,
        "required_permission": "terreno.view"
    },
]

# Widget da registrare con la platform
WIDGETS = [
    {
        "id": "immobili.stats",
        "title": "Statistiche Immobili",
        "component": "ImmobiliStatsWidget",
        "description": "Panoramica generale delle unità immobiliari, proprietari e condomini",
        "default_width": 6,
        "default_height": 4,
        "category": "stats",
        "module_id": "immobili",
        "required_permission": "immobile.view"
    },
    {
        "id": "immobili.certificati_scadenza",
        "title": "Certificati in Scadenza",
        "component": "CertificatiScadenzaWidget",
        "description": "Monitoraggio certificati energetici in scadenza o scaduti",
        "default_width": 6,
        "default_height": 4,
        "category": "alerts",
        "module_id": "immobili",
        "required_permission": "certificato_energetico.view"
    },
]

__all__ = ["manifest", "models", "ROUTERS", "MENU_ITEMS", "WIDGETS"]


def register_module(app):
    """
    Called by the module loader to register this module.
    """
    print("[Immobili Module] Registering module...")
    print("[Immobili Module] Providing property management functionality")
    print("[Immobili Module] Registration complete!")
