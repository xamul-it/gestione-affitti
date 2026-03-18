"""
Manifest for Immobili (Real Estate Properties) Module

Conforme agli standard di architettura moduli v1.0
"""

manifest = {
    # Campi obbligatori
    "name": "Immobili",
    "technical_name": "immobili",
    "version": "2025022002",
    "module_short_code": "IMMO",  # 4 caratteri - usato come prefisso per tutte le tabelle
    "schema_target": "public + tenant",  # Tabelle sia in public che in tenant schema
    "migrations_path": "migrations/",
    "seeds_path": "seeds/",
    "endpoints": {
        "register": ":register",  # Funzione in __init__.py per registrazione modulo (crea tabelle public + seed)
        "install": ":install",    # Funzione in __init__.py per installazione su tenant (crea tabelle tenant)
    },

    # Campi opzionali
    "author": "Gestione Affitti Team",
    "sequence": 20,
    "license": "proprietary",
    "installable": True,
    "auto_install": False,
    "application": True,

    # Dipendenze
    "dependencies": ["anagrafica_italiana"],
    "optional_depends": [],

    # Models forniti dal modulo (con prefisso immo_)
    "models": [
        # Domain data (public schema)
        "immo_categorie_catastali",
        "immo_tipologie_terreno",
        # Tenant data
        "immo_tipologie_terreno_overrides",
        "immo_terreni",
        "immo_unita_immobiliari",
        "immo_condomini",
        "immo_proprietari",
        "immo_diritti_immobile",
        "immo_certificati_energetici",
        "immo_tabelle_millesimali",
        "immo_millesimi_unita",
        "immo_tipo_immobile_categoria_map",
    ],

    # Public domain tables required for registration
    "public_tables": [
        "immo_categorie_catastali",
        "immo_tipologie_terreno",
    ],

    # Tenant schema tables (created during tenant install)
    "tenant_tables": [
        "immo_condomini",
        "immo_unita_immobiliari",
        "immo_proprietari",
        "immo_diritti_immobile",
        "immo_certificati_energetici",
        "immo_tabelle_millesimali",
        "immo_millesimi_unita",
        "immo_tipologie_terreno_overrides",
        "immo_terreni",
        "immo_tipo_immobile_categoria_map",
    ],

    # DDL for override tables (reference public domain tables, created directly in tenant schema)
    "override_tables_ddl": {
        "immo_tipologie_terreno_overrides": """
            CREATE TABLE IF NOT EXISTS {schema}.immo_tipologie_terreno_overrides (
                id SERIAL PRIMARY KEY,
                tipologia_id INTEGER NOT NULL REFERENCES public.immo_tipologie_terreno(id) ON DELETE CASCADE,
                codice VARCHAR(20),
                nome VARCHAR(100),
                descrizione TEXT,
                attivo BOOLEAN,
                is_deleted BOOLEAN NOT NULL DEFAULT false,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ,
                UNIQUE(tipologia_id)
            )
        """,
    },

    # API prefix
    "api_prefix": "/immobili",

    # Permissions
    "permissions": [
        "immobile.view",
        "immobile.create",
        "immobile.edit",
        "immobile.delete",
        "proprietario.view",
        "proprietario.create",
        "proprietario.edit",
        "proprietario.delete",
        "condominio.view",
        "condominio.create",
        "condominio.edit",
        "condominio.delete",
        "certificato_energetico.view",
        "certificato_energetico.create",
        "certificato_energetico.edit",
        "certificato_energetico.delete",
        "terreno.view",
        "terreno.create",
        "terreno.edit",
        "terreno.delete",
    ],

    # Dashboard widgets
    "widgets": [
        {
            "id": "immobili.stats",
            "title": "Statistiche Immobili",
            "component": "ImmobiliStatsWidget",
            "default_width": 6,
            "default_height": 4,
            "category": "stats",
            "required_permission": "immobile.view",
        },
        {
            "id": "immobili.certificati_scadenza",
            "title": "Certificati in Scadenza",
            "component": "CertificatiScadenzaWidget",
            "default_width": 6,
            "default_height": 4,
            "category": "alerts",
            "required_permission": "certificato_energetico.view",
        },
    ],

    # Menu items
    "menu_items": [
        {
            "id": "immobili.unita",
            "label": "Unità Immobiliari",
            "path": "/unita-immobiliari",
            "icon": "building",
            "order_index": 10,
            "required_permission": "immobile.view"
        },
        {
            "id": "immobili.terreni",
            "label": "Terreni",
            "path": "/terreni",
            "icon": "leaf",
            "order_index": 15,
            "required_permission": "terreno.view"
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
            "id": "immobili.categorie_catastali",
            "label": "Categorie Catastali",
            "path": "/categorie-catastali",
            "icon": "list",
            "order_index": 90,
            "required_permission": "platform.admin",
            "is_domain_data": True,
        },
        {
            "id": "immobili.tipologie_terreno",
            "label": "Tipologie Terreno",
            "path": "/tipologie-terreno",
            "icon": "leaf",
            "order_index": 95,
            "required_permission": "platform.admin",
            "is_domain_data": True,
        },
    ],
}
