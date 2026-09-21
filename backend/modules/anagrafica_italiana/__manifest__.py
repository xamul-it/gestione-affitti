"""
Manifest for Anagrafica Italiana (Italian Registry) Module

This module provides Italian-specific person/company registry functionality.
It manages personal and company data according to Italian regulations
(codice fiscale, partita IVA, etc.).
"""

manifest = {
    "name": "Anagrafica",
    "technical_name": "anagrafica_italiana",
    "version": "2026011506",
    "module_short_code": "anag",
    "schema_target": "public + tenant",
    "migrations_path": "migrations/versions",
    "seeds_path": "seeds",
    "endpoints": {
        "register": "seeds.seed_public:seed_public",
        "install": "seeds.seed_tenant:seed_tenant",
    },
    "author": "Gestione Affitti Team",
    # Module configuration
    "sequence": 10,

    # Dependencies - this module has no dependencies on other business modules
    "dependencies": [],

    # Models provided by this module
    "models": [
        "soggetto_anagrafico",
        "comune_italia",
    ],

    # Public domain tables required for registration
    #
    # NOTE: the document registry (Documento, DocumentoFile, TipoDocumento,
    # StatoDocumento + their tenant overrides) moved to app/core/platform/models
    # (now core_tipi_documento, core_stati_documento, core_documenti,
    # core_documenti_files, core_tipi_documento_overrides,
    # core_stati_documento_overrides) — it's a core platform service per
    # docs/superpowers/specs/2026-09-14-module-communication-architecture-design.md,
    # not anagrafica_italiana's. Those tables are created for every tenant by
    # core Alembic migrations (2026092101/2026092102), not by this manifest,
    # and are intentionally absent from public_tables/tenant_tables/
    # override_tables_ddl below.
    "public_tables": [
        "anag_comuni_italia",
        "anag_ruoli_azienda_tipi",
    ],

    # Tenant schema tables (created during tenant install)
    "tenant_tables": [
        "anag_soggetti_anagrafici",
        "anag_ruoli_azienda",
        "anag_comuni_italia_overrides",
        "anag_ruoli_azienda_tipi_overrides",
    ],

    # DDL for override tables (reference public domain tables, created directly in tenant schema)
    "override_tables_ddl": {
        "anag_comuni_italia_overrides": """
            CREATE TABLE IF NOT EXISTS {schema}.anag_comuni_italia_overrides (
                id SERIAL PRIMARY KEY,
                comune_id INTEGER NOT NULL REFERENCES public.anag_comuni_italia(id) ON DELETE CASCADE,
                nome VARCHAR(100),
                nome_normalized VARCHAR(100),
                codice_istat VARCHAR(10),
                codice_catastale VARCHAR(10),
                cap VARCHAR(10),
                provincia_sigla VARCHAR(2),
                provincia_nome VARCHAR(100),
                regione VARCHAR(100),
                latitudine NUMERIC(10, 7),
                longitudine NUMERIC(10, 7),
                is_deleted BOOLEAN NOT NULL DEFAULT false,
                deleted_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ,
                UNIQUE(comune_id)
            )
        """,
        "anag_ruoli_azienda_tipi_overrides": """
            CREATE TABLE IF NOT EXISTS {schema}.anag_ruoli_azienda_tipi_overrides (
                id SERIAL PRIMARY KEY,
                ruolo_tipo_id INTEGER NOT NULL REFERENCES public.anag_ruoli_azienda_tipi(id) ON DELETE CASCADE,
                nome VARCHAR(100),
                descrizione VARCHAR(500),
                attivo BOOLEAN,
                is_deleted BOOLEAN NOT NULL DEFAULT false,
                deleted_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ,
                UNIQUE(ruolo_tipo_id)
            )
        """,
    },

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

    # Document types with parsing support
    "document_types": [
        {
            "codice": "CARTA_IDENTITA",
            "nome": "Carta d'Identità",
            "categoria": "identita",
            "richiede_scadenza": True,
            "parsing_service": "mrz",
            "parsing_config": {
                "mrz_format": "td1",
                "rotate_mode": "auto",
                "extract_photo": True,
            }
        },
        {
            "codice": "PASSAPORTO",
            "nome": "Passaporto",
            "categoria": "identita",
            "richiede_scadenza": True,
            "parsing_service": "mrz",
            "parsing_config": {
                "mrz_format": "td3",
                "rotate_mode": "auto",
                "extract_photo": True,
            }
        },
        {
            "codice": "PATENTE_GUIDA",
            "nome": "Patente di Guida",
            "categoria": "identita",
            "richiede_scadenza": True,
            "parsing_service": "mrz",
            "parsing_config": {
                "mrz_format": "td1",
                "rotate_mode": "auto",
            }
        },
        {
            "codice": "PERMESSO_SOGGIORNO",
            "nome": "Permesso di Soggiorno",
            "categoria": "identita",
            "richiede_scadenza": True,
            "parsing_service": "mrz",
            "parsing_config": {
                "mrz_format": "td1",
                "rotate_mode": "auto",
            }
        },
        {
            "codice": "CODICE_FISCALE",
            "nome": "Tessera Codice Fiscale",
            "categoria": "identita",
            "richiede_scadenza": False,
        },
        {
            "codice": "VISURA_CAMERALE",
            "nome": "Visura Camerale",
            "categoria": "aziendale",
            "richiede_scadenza": False,
        },
        {
            "codice": "ATTO_COSTITUTIVO",
            "nome": "Atto Costitutivo",
            "categoria": "aziendale",
            "richiede_scadenza": False,
        },
        {
            "codice": "STATUTO",
            "nome": "Statuto Societario",
            "categoria": "aziendale",
            "richiede_scadenza": False,
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
            "id": "anagrafica.tipi_documento",
            "label": "Tipi Documento",
            "path": "/anagrafiche/domini/tipi-documento",
            "icon": "file-text",
            "order_index": 85,
            "required_permission": "soggetto.view",
            "is_domain_data": True,
        },
        {
            "id": "anagrafica.stati_documento",
            "label": "Stati Documento",
            "path": "/anagrafiche/domini/stati-documento",
            "icon": "check-circle",
            "order_index": 87,
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
