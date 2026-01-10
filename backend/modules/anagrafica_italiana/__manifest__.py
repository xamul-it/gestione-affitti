"""
Manifest for Anagrafica Italiana (Italian Registry) Module

This module provides Italian-specific person/company registry functionality.
It manages personal and company data according to Italian regulations
(codice fiscale, partita IVA, etc.).
"""

manifest = {
    "name": "Anagrafica",
    "technical_name": "anagrafica_italiana",
    "version": "1.0.0",
    "description": "Gestione anagrafica soggetti italiani (persone fisiche e giuridiche)",
    "author": "Gestione Affitti Team",
    "icon": "users",

    # Module configuration
    "category": "registry",
    "sequence": 10,

    # Dependencies - this module has no dependencies on other business modules
    "dependencies": [],

    # Models provided by this module
    "models": [
        "soggetto_anagrafico",
        "comune_italia",
        "tipo_documento",
    ],

    # API routes
    "api_prefix": "/anagrafica",

    # Frontend configuration
    "frontend_config": {
        "menu_icon": "users",
        "color": "#3498db",
    },

    # Dashboard widgets
    "widgets": [
        {
            "id": "anagrafica_italiana.stats_soggetti",
            "title": "Statistiche Anagrafiche",
            "component": "StatsSoggettiWidget",
            "default_width": 6,
            "default_height": 4,
            "category": "stats",
            "required_permission": "soggetto.view",
            "description": "Panoramica delle anagrafiche registrate (persone fisiche e giuridiche)",
        },
    ],

    # Menu items for this module - flat structure (no parent-child)
    "menu_items": [
        {
            "id": "anagrafica.soggetti",
            "label": "Anagrafiche",
            "path": "/anagrafiche/lista",
            "icon": "users",
            "order_index": 10,
            "required_permission": "soggetto.view",
        },
        {
            "id": "anagrafica.persone_fisiche",
            "label": "Persone Fisiche",
            "path": "/anagrafiche/persone-fisiche",
            "icon": "user",
            "order_index": 20,
            "required_permission": "soggetto.view",
        },
        {
            "id": "anagrafica.persone_giuridiche",
            "label": "Persone Giuridiche",
            "path": "/anagrafiche/persone-giuridiche",
            "icon": "building-2",
            "order_index": 30,
            "required_permission": "soggetto.view",
        },
        {
            "id": "anagrafica.ruoli_azienda",
            "label": "Ruoli Azienda",
            "path": "/anagrafiche/ruoli-azienda",
            "icon": "briefcase",
            "order_index": 40,
            "required_permission": "soggetto.view",
        },
        {
            "id": "anagrafica.comuni",
            "label": "Comuni Italia",
            "path": "/anagrafiche/comuni",
            "icon": "map-pin",
            "order_index": 80,
            "required_permission": "soggetto.view",
            "is_domain_data": True,
        },
        {
            "id": "anagrafica.ruoli_tipi",
            "label": "Tipi Ruolo",
            "path": "/anagrafiche/domini/ruoli-azienda",
            "icon": "list",
            "order_index": 90,
            "required_permission": "soggetto.view",
            "is_domain_data": True,
        },
    ],

    # Permissions required by this module
    "permissions": [
        {"name": "soggetto.view", "description": "Visualizzare soggetti anagrafici"},
        {"name": "soggetto.create", "description": "Creare soggetti anagrafici"},
        {"name": "soggetto.edit", "description": "Modificare soggetti anagrafici"},
        {"name": "soggetto.delete", "description": "Eliminare soggetti anagrafici"},
    ],

    # Roles provided by this module
    "roles": [
        {
            "name": "registry_operator",
            "description": "Operatore Anagrafica",
            "permissions": [
                "soggetto.view",
                "soggetto.create",
                "soggetto.edit",
            ]
        },
        {
            "name": "registry_admin",
            "description": "Amministratore Anagrafica",
            "permissions": [
                "soggetto.view",
                "soggetto.create",
                "soggetto.edit",
                "soggetto.delete",
            ]
        },
    ],

    # Available roles that other modules can assign to soggetti
    "ruoli_disponibili": [
        {
            "technical_name": "proprietario",
            "nome_ruolo": "Proprietario",
            "descrizione": "Proprietario di immobili",
            "modulo_origine": "immobili",
        },
        {
            "technical_name": "affittuario",
            "nome_ruolo": "Affittuario",
            "descrizione": "Affittuario/Inquilino",
            "modulo_origine": "affitti_lungo",
        },
        {
            "technical_name": "tecnico",
            "nome_ruolo": "Tecnico",
            "descrizione": "Tecnico/Manutentore",
            "modulo_origine": "affitti_lungo",
        },
    ],
}
