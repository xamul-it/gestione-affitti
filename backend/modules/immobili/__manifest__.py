"""
Manifest for Immobili (Real Estate Properties) Module
"""

manifest = {
    "name": "Immobili",
    "technical_name": "immobili",
    "version": "1.0.0",
    "description": "Gestione completa immobili, condomini, proprietari e dati catastali",
    "author": "Gestione Affitti Team",
    "icon": "building",
    "category": "real_estate",
    "sequence": 20,
    "dependencies": ["anagrafica_italiana"],
    "models": [
        "categoria_catastale",
        "comune_italia",
        "unita_immobiliare",
        "condominio",
        "proprietario",
        "diritto_immobile",
        "certificato_energetico",
    ],
    "api_prefix": "/immobili",

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
}
