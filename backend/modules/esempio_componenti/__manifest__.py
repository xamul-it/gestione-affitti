"""
Manifest for Esempio Componenti Module

Modulo dimostrativo per esemplificare l'uso dei componenti trasversali
della piattaforma: DataTable configurabile, Import/Export, Domini.

Module Standard Compliance:
- module_short_code: esem
- schema_target: public + tenant
"""

manifest = {
    "name": "Esempio Componenti",
    "technical_name": "esempio_componenti",
    "version": "2026011801",
    "module_short_code": "esem",
    "schema_target": "public + tenant",
    "migrations_path": "migrations/versions",
    "seeds_path": "seeds",
    "endpoints": {
        "register": "seeds.seed_public:seed_all_public",
        "install": "seeds.seed_tenant:seed_tenant",
    },
    "description": """
        Modulo dimostrativo che esemplifica l'uso dei componenti core della piattaforma:
        - DataTable configurabile con selezione colonne
        - Import/Export dati CSV/Excel
        - Domini (dati condivisi in public schema)
        - Entità tenant (dati isolati per tenant)
    """,
    "author": "Platform Team",
    "icon": "puzzle",

    "category": "base",
    "sequence": 5,

    # No dependencies - this is a standalone example module
    "dependencies": [],

    # Models provided by this module
    "models": [
        "CategoriaEsempio",      # Domain data (public schema)
        "PrioritaEsempio",       # Domain data (public schema)
        "ElementoEsempio",       # Tenant data
    ],

    # Public domain tables required for registration
    "public_tables": [
        "esem_categorie_esempio",
        "esem_priorita_esempio",
    ],

    # Tenant tables (created in tenant schema when module is enabled)
    "tenant_tables": [
        "elementi_esempio",
    ],

    # API route prefix
    "api_prefix": "/esempio",

    # Frontend configuration
    "frontend_config": {
        "menu_icon": "puzzle",
        "color": "#9b59b6",
    },

    # Permissions
    "permissions": [
        {"name": "esempio.view", "description": "Visualizzare elementi esempio"},
        {"name": "esempio.create", "description": "Creare elementi esempio"},
        {"name": "esempio.edit", "description": "Modificare elementi esempio"},
        {"name": "esempio.delete", "description": "Eliminare elementi esempio"},
        {"name": "esempio.import", "description": "Importare dati esempio"},
        {"name": "esempio.export", "description": "Esportare dati esempio"},
    ],

    # Dashboard widgets
    "widgets": [
        {
            "id": "esempio_componenti.stats",
            "title": "Statistiche Elementi",
            "component": "EsempioStatsWidget",
            "description": "Panoramica degli elementi di esempio",
            "default_width": 4,
            "default_height": 3,
            "category": "stats",
            "required_permission": "esempio.view",
        },
    ],

    # Menu items - flat structure
    "menu_items": [
        {
            "id": "esempio.elementi",
            "label": "Elementi",
            "path": "/esempio/elementi",
            "icon": "list",
            "order_index": 10,
            "required_permission": "esempio.view",
        },
        {
            "id": "esempio.categorie",
            "label": "Categorie",
            "path": "/esempio/categorie",
            "icon": "tag",
            "order_index": 20,
            "required_permission": "esempio.view",
            "is_domain_data": True,
        },
        {
            "id": "esempio.priorita",
            "label": "Priorità",
            "path": "/esempio/priorita",
            "icon": "alert-triangle",
            "order_index": 30,
            "required_permission": "esempio.view",
            "is_domain_data": True,
        },
    ],
}
