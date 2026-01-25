"""
Manifest for Affitti Lungo (Long-term Rental Management) Module

This is a built-in module (legacy location in app/modules/).
"""

manifest = {
    "name": "Affitti",
    "technical_name": "affitti_lungo",
    "version": "2025022001",
    "module_short_code": "alng",
    "schema_target": "tenant",
    "migrations_path": "migrations/versions",
    "author": "Gestione Affitti Team",
    "sequence": 100,  # Built-in module, higher sequence

    # Dependencies on other modules
    "dependencies": [
        "immobili",              # UnitaImmobiliare, Condominio, Proprietario
        "anagrafica_italiana",   # SoggettoAnagrafico
    ],

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

    # API routes (handled by main.py for legacy module)
    "api_prefix": "/api/v1",  # Legacy - routes registered directly in main.py

    # This is a built-in module
    "builtin": True,
    "location": "app/modules/affitti_lungo",
}
