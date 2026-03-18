"""
Manifest for Affitti Lungo (Long-term Rental Management) Module
"""

manifest = {
    "name": "Affitti",
    "technical_name": "affitti_lungo",
    "version": "2025022001",
    "module_short_code": "alng",
    "schema_target": "tenant",
    "migrations_path": "migrations/versions",
    "author": "Gestione Affitti Team",
    "sequence": 100,

    # Dependencies on other modules
    "dependencies": [
        "immobili",              # UnitaImmobiliare, Condominio, Proprietario
        "anagrafica_italiana",   # SoggettoAnagrafico
    ],

    # Entry points called by module lifecycle
    "endpoints": {
        "register_roles": "roles:register_roles",  # called at module register
    },

    # Models provided
    "models": [
        "affittuario",
        "contratto",
        "incasso",
        "spesa",
        "tecnico",
        "ripartizione_spesa",
        "documento",
    ],

    # Tenant schema tables (created during tenant install)
    "tenant_tables": [
        "affittuari",
        "contratti",
        "incassi",
        "spese",
        "ripartizioni_spese",
        "tecnici",
    ],

    # No public tables for this module (schema_target = "tenant")
    "public_tables": [],

    # No override tables for this module
    "override_tables_ddl": {},

    # API prefix
    "api_prefix": "/api/v1",

    # Permissions
    "permissions": [
        {"name": "contratto.view", "description": "Visualizzare contratti di affitto"},
        {"name": "contratto.create", "description": "Creare contratti di affitto"},
        {"name": "contratto.edit", "description": "Modificare contratti di affitto"},
        {"name": "contratto.delete", "description": "Eliminare contratti di affitto"},
        {"name": "affittuario.view", "description": "Visualizzare affittuari"},
        {"name": "affittuario.create", "description": "Creare affittuari"},
        {"name": "affittuario.edit", "description": "Modificare affittuari"},
        {"name": "affittuario.delete", "description": "Eliminare affittuari"},
        {"name": "incasso.view", "description": "Visualizzare incassi"},
        {"name": "incasso.create", "description": "Registrare incassi"},
        {"name": "incasso.edit", "description": "Modificare incassi"},
        {"name": "incasso.delete", "description": "Eliminare incassi"},
        {"name": "spesa.view", "description": "Visualizzare spese"},
        {"name": "spesa.create", "description": "Registrare spese"},
        {"name": "spesa.edit", "description": "Modificare spese"},
        {"name": "spesa.delete", "description": "Eliminare spese"},
        {"name": "tecnico.view", "description": "Visualizzare tecnici"},
        {"name": "tecnico.create", "description": "Creare tecnici"},
        {"name": "tecnico.edit", "description": "Modificare tecnici"},
        {"name": "tecnico.delete", "description": "Eliminare tecnici"},
    ],

    # Available roles registered in the system
    "ruoli_disponibili": [
        {
            "technical_name": "proprietario",
            "nome_ruolo": "Proprietario",
            "descrizione": "Proprietario di immobili",
            "tabella_specializzazione": "proprietari",
            "modulo_origine": "affitti_lungo",
        },
        {
            "technical_name": "affittuario",
            "nome_ruolo": "Affittuario / Inquilino",
            "descrizione": "Affittuario o inquilino di un immobile",
            "tabella_specializzazione": "affittuari",
            "modulo_origine": "affitti_lungo",
        },
        {
            "technical_name": "tecnico",
            "nome_ruolo": "Tecnico",
            "descrizione": "Tecnico manutentore",
            "tabella_specializzazione": "tecnici",
            "modulo_origine": "affitti_lungo",
        },
    ],

    # Dashboard widgets
    "widgets": [
        {
            "id": "affitti.contratti_scadenza",
            "title": "Contratti in Scadenza",
            "component": "ContrattiScadenzaWidget",
            "description": "Contratti di locazione in scadenza nei prossimi 90 giorni",
            "default_width": 6,
            "default_height": 4,
            "category": "alerts",
            "required_permission": "contratto.view",
        },
        {
            "id": "affitti.stats_immobili",
            "title": "Statistiche Immobili",
            "component": "StatsImmobiliWidget",
            "description": "Panoramica generale del portafoglio immobiliare",
            "default_width": 3,
            "default_height": 3,
            "category": "stats",
            "required_permission": "immobile.view",
        },
        {
            "id": "affitti.incassi_mensili",
            "title": "Incassi Mensili",
            "component": "IncassiMensiliWidget",
            "description": "Grafico degli incassi mensili degli ultimi 6 mesi",
            "default_width": 6,
            "default_height": 4,
            "category": "charts",
            "required_permission": "incasso.view",
        },
        {
            "id": "affitti.spese_recenti",
            "title": "Ultime Spese",
            "component": "SpeseRecentiWidget",
            "description": "Lista delle ultime spese registrate",
            "default_width": 3,
            "default_height": 4,
            "category": "stats",
            "required_permission": "spesa.view",
        },
    ],

    # Menu items
    "menu_items": [
        {
            "id": "affitti.contratti",
            "label": "Contratti",
            "path": "/contratti",
            "icon": "file-text",
            "order_index": 20,
            "required_permission": "contratto.view",
        },
        {
            "id": "affitti.affittuari",
            "label": "Affittuari",
            "path": "/affittuari",
            "icon": "users",
            "order_index": 30,
            "required_permission": "affittuario.view",
        },
        {
            "id": "affitti.incassi",
            "label": "Incassi",
            "path": "/incassi",
            "icon": "trending-up",
            "order_index": 40,
            "required_permission": "incasso.view",
        },
        {
            "id": "affitti.spese",
            "label": "Spese",
            "path": "/spese",
            "icon": "trending-down",
            "order_index": 50,
            "required_permission": "spesa.view",
        },
        {
            "id": "affitti.tecnici",
            "label": "Tecnici",
            "path": "/tecnici",
            "icon": "wrench",
            "order_index": 60,
            "required_permission": "tecnico.view",
        },
    ],
}
