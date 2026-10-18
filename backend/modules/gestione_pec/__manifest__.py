"""
Manifest for Gestione PEC (PEC Inbox Management) Module
"""

manifest = {
    "name": "Gestione PEC",
    "technical_name": "gestione_pec",
    "version": "2026031901",
    "module_short_code": "gpec",
    "schema_target": "tenant",
    "migrations_path": "migrations/versions",
    "seeds_path": "seeds",
    "author": "Modstack Team",
    "sequence": 200,

    # No dependencies on other business modules
    "dependencies": [],

    # Entry points called by module lifecycle
    "endpoints": {
        "register": "seeds:seed_public",
        "install": "seeds:seed_tenant",
        "register_roles": "roles:register_roles",
    },

    # Tenant schema tables (created during tenant install)
    "tenant_tables": [
        "pec_caselle",
        "pec_utenti_abilitati",
        "pec_messaggi",
        "pec_audit_accessi",
        "pec_audit_risposte",
        "pec_notifiche_log",
    ],

    # No public tables for this module (schema_target = "tenant")
    "public_tables": [],

    # No override tables for this module
    "override_tables_ddl": {},

    # API prefix
    "api_prefix": "/api/v1",

    # Permissions
    "permissions": [
        {"name": "pec.admin", "description": "Configurare caselle PEC e utenti abilitati"},
        {"name": "pec.read", "description": "Leggere messaggi PEC"},
        {"name": "pec.reply", "description": "Rispondere a messaggi PEC"},
        {"name": "pec.audit.view", "description": "Visualizzare log di audit PEC"},
    ],

    # Available roles registered in the system
    "ruoli_disponibili": [
        {"codice": "pec_admin", "nome_display": "PEC Amministratore"},
        {"codice": "pec_operator", "nome_display": "PEC Operatore"},
        {"codice": "pec_viewer", "nome_display": "PEC Lettore"},
    ],

    # Menu items
    "menu_items": [
        {
            "id": "pec.inbox",
            "label": "Caselle PEC",
            "icon": "mail",
            "path": "/pec",
            "required_permission": "pec.read",
            "order_index": 50,
        },
        {
            "id": "pec.admin",
            "label": "Configura PEC",
            "icon": "cog",
            "path": "/pec/admin",
            "required_permission": "pec.admin",
            "order_index": 60,
        },
    ],

    # Dashboard widgets
    "widgets": [
        {
            "id": "pec.summary",
            "title": "PEC - Messaggi non letti",
            "component": "PecSummaryWidget",
            "description": "Riepilogo dei messaggi PEC non letti",
            "default_width": 4,
            "default_height": 3,
            "category": "stats",
            "required_permission": "pec.read",
        },
    ],
}
