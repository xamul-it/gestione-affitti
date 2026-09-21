# Import models FIRST to ensure they're loaded before routes
from . import models


def get_routers():
    """
    Lazily import routers to avoid circular imports at module import time.
    """
    from .routes import (
        affittuari_router,
        contratti_router,
        spese_router,
        incassi_router,
        tecnici_router,
        documenti_router,
        ripartizione_spesa_router,
        search_router,
    )
    return [
        affittuari_router,
        contratti_router,
        spese_router,
        incassi_router,
        tecnici_router,
        documenti_router,
        ripartizione_spesa_router,
        search_router,
    ]


# Routers provided by this module (lazy)
ROUTERS = []

# Menu items da registrare con la platform
# Attualmente vuoto - le voci verranno aggiunte quando il modulo sarà attivo
MENU_ITEMS = [
    # {
    #     "id": "affitti.dashboard",
    #     "label": "Dashboard Affitti",
    #     "path": "/modules/affitti_lungo/dashboard",
    #     "icon": "📊",
    #     "order_index": 5,
    #     "required_permission": None
    # },
    # {
    #     "id": "affitti.contratti",
    #     "label": "Contratti",
    #     "path": "/contratti",
    #     "icon": "file-contract",
    #     "order_index": 20,
    #     "required_permission": "contratto.view"
    # },
    # {
    #     "id": "affitti.affittuari",
    #     "label": "Affittuari",
    #     "path": "/affittuari",
    #     "icon": "users",
    #     "order_index": 30,
    #     "required_permission": "affittuario.view"
    # },
    # {
    #     "id": "affitti.proprietari",
    #     "label": "Proprietari",
    #     "path": "/proprietari",
    #     "icon": "user-tie",
    #     "order_index": 40,
    #     "required_permission": "proprietario.view"
    # },
    # {
    #     "id": "affitti.condomini",
    #     "label": "Condomini",
    #     "path": "/condomini",
    #     "icon": "building-columns",
    #     "order_index": 50,
    #     "required_permission": "condominio.view"
    # },
    # {
    #     "id": "affitti.gestione",
    #     "label": "Gestione",
    #     "path": "#",
    #     "icon": "cog",
    #     "order_index": 60,
    #     "required_permission": None  # Visibile a tutti (submenu container)
    # },
    # {
    #     "id": "affitti.spese",
    #     "label": "Spese",
    #     "path": "/spese",
    #     "parent_id": "affitti.gestione",
    #     "order_index": 1,
    #     "required_permission": "spesa.view"
    # },
    # {
    #     "id": "affitti.incassi",
    #     "label": "Incassi",
    #     "path": "/incassi",
    #     "parent_id": "affitti.gestione",
    #     "order_index": 2,
    #     "required_permission": "incasso.view"
    # },
    # {
    #     "id": "affitti.tecnici",
    #     "label": "Tecnici",
    #     "path": "/tecnici",
    #     "parent_id": "affitti.gestione",
    #     "order_index": 3,
    #     "required_permission": "tecnico.view"
    # },
    # {
    #     "id": "affitti.documenti",
    #     "label": "Documenti",
    #     "path": "/documenti",
    #     "parent_id": "affitti.gestione",
    #     "order_index": 4,
    #     "required_permission": "documento.view"
    # },
]

# Widget da registrare con la platform
WIDGETS = [
    {
        "id": "affitti.contratti_scadenza",
        "title": "Contratti in Scadenza",
        "component": "ContrattiScadenzaWidget",
        "description": "Visualizza i contratti di locazione in scadenza nei prossimi 90 giorni",
        "default_width": 6,
        "default_height": 4,
        "category": "alerts",
        "required_permission": "contratto.view"
    },
    {
        "id": "affitti.stats_immobili",
        "title": "Statistiche Immobili",
        "component": "StatsImmobiliWidget",
        "description": "Panoramica generale del portafoglio immobiliare",
        "default_width": 3,
        "default_height": 3,
        "category": "stats",
        "required_permission": "immobile.view"
    },
    {
        "id": "affitti.incassi_mensili",
        "title": "Incassi Mensili",
        "component": "IncassiMensiliWidget",
        "description": "Grafico degli incassi mensili degli ultimi 6 mesi",
        "default_width": 6,
        "default_height": 4,
        "category": "charts",
        "required_permission": "incasso.view"
    },
    {
        "id": "affitti.spese_recenti",
        "title": "Ultime Spese",
        "component": "SpeseRecentiWidget",
        "description": "Lista delle ultime spese registrate",
        "default_width": 3,
        "default_height": 4,
        "category": "stats",
        "required_permission": "spesa.view"
    },
]

__all__ = [
    # Models
    "models",
    # Routers (list for auto-discovery)
    "ROUTERS",
    "get_routers",
    "MENU_ITEMS",
    "WIDGETS",
]
