"""
Manifest for Affitti Lungo (Long-term Rental Management) Module

This is a built-in module (legacy location in app/modules/).
"""

manifest = {
    "name": "Affitti",
    "technical_name": "affitti_lungo",
    "version": "1.0.0",
    "description": "Gestione completa affitti a lungo termine: contratti, affittuari, incassi, spese",
    "author": "Gestione Affitti Team",
    "icon": "briefcase",

    "category": "rental",
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
