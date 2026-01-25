"""
Affitti Brevi Module Manifest

Short-term rental management module with unified calendar,
iCal synchronization, guest management, and compliance tracking.
"""

manifest = {
    "name": "Gestione Affitti Brevi",
    "technical_name": "affitti_brevi",
    "version": "2025021701",
    "module_short_code": "abrev",
    "schema_target": "tenant",
    "migrations_path": "migrations/versions",
    "seeds_path": "seeds",
    "table_prefix": "ab",
    "endpoints": {
        "register": ":register",
        "install": ":install",
    },
    "status": "production",
    "author": "Gestione Affitti Platform",
    "sequence": 20,
    "installable": True,
    "auto_install": False,
    "application": True,

    # Module dependencies
    "dependencies": [
        "immobili",            # For UnitaImmobiliare
        "anagrafica_italiana"  # For SoggettoAnagrafico (guests)
    ],
    "depends": [
        "immobili",
        "anagrafica_italiana",
    ],

    # Models provided by this module
    "models": [
        # Channel configuration
        "canale",
        # Calendar and bookings
        "calendario_canale",
        "prenotazione",
        "blocco_calendario",
        # Stay management
        "soggiorno",
        "ospite_soggiorno",
        # Tourist tax
        "tassa_soggiorno_config",
        "tassa_soggiorno_scaglione",
        "tassa_soggiorno",
        # Communications and compliance
        "comunicazione",
        "attivita_schedulata",
    ],

    # API route prefix
    "api_prefix": "/affitti-brevi",

    # API routes
    "api_routes": [
        {"prefix": "/canali", "description": "Booking channel management"},
        {"prefix": "/calendari", "description": "Property-channel calendar links"},
        {"prefix": "/calendario-unificato", "description": "Unified calendar view"},
        {"prefix": "/prenotazioni", "description": "Booking management"},
        {"prefix": "/soggiorni", "description": "Stay operations and guest management"},
        {"prefix": "/sync", "description": "iCal synchronization"},
        {"prefix": "/tasse", "description": "Tourist tax configuration and calculation"},
    ],

    # Features
    "features": {
        "unified_calendar": True,        # Single calendar per property aggregating all channels
        "ical_sync": True,               # Automatic iCal synchronization
        "conflict_detection": True,       # Overlapping booking detection
        "guest_management": True,         # Guest data collection for compliance
        "self_service_checkin": True,    # Guest self-service data entry
        "tourist_tax": True,             # Tax calculation with exemptions
        "police_communications": True,    # Alloggiati Web integration
        "istat_statistics": True,        # ISTAT reporting
        "scheduled_activities": True,    # Recurring tasks
    },

    # Visual conventions (from analysis)
    "calendar_visual": {
        "channels": {
            "AIRBNB": {"color": "#FF5A5F", "symbol": "A"},
            "BOOKING_COM": {"color": "#003580", "symbol": "B"},
            "VRBO": {"color": "#5D3B9E", "symbol": "V"},
            "DIRETTO": {"color": "#2E8B57", "symbol": "D"},
            "ALTRO": {"color": "#808080", "symbol": "?"},
        },
        "states": {
            "LIBERO": {"display": "○", "description": "Available (border only)"},
            "PRENOTATO": {"display": "●", "description": "Booked (filled)"},
            "CHIUSO": {"display": "✕", "description": "Closed/unavailable"},
        },
        "aggregate_states": {
            "LIBERO": "All channels free",
            "OCCUPATO": "At least one booking",
            "NON_DISPONIBILE": "Property blocked",
            "CONFLITTO": "Multiple bookings - requires resolution",
        }
    },

    # Permissions
    "permissions": [
        {
            "code": "affitti_brevi.view",
            "name": "Visualizza Affitti Brevi",
            "description": "Può visualizzare prenotazioni, ospiti e calendari"
        },
        {
            "code": "affitti_brevi.create",
            "name": "Crea Affitti Brevi",
            "description": "Può creare prenotazioni e soggiorni"
        },
        {
            "code": "affitti_brevi.edit",
            "name": "Modifica Affitti Brevi",
            "description": "Può modificare prenotazioni, ospiti e soggiorni"
        },
        {
            "code": "affitti_brevi.delete",
            "name": "Elimina Affitti Brevi",
            "description": "Può eliminare prenotazioni e soggiorni"
        },
        {
            "code": "affitti_brevi.checkin",
            "name": "Gestione Check-in",
            "description": "Può eseguire check-in e check-out"
        },
        {
            "code": "affitti_brevi.sync",
            "name": "Sincronizzazione iCal",
            "description": "Può attivare sincronizzazione manuale dei calendari"
        },
        {
            "code": "affitti_brevi.tax_config",
            "name": "Configurazione Tasse",
            "description": "Può configurare le tariffe della tassa di soggiorno"
        },
        {
            "code": "affitti_brevi.tax_override",
            "name": "Override Tasse",
            "description": "Può sovrascrivere manualmente il calcolo delle tasse"
        },
        {
            "code": "affitti_brevi.communications",
            "name": "Comunicazioni Obbligatorie",
            "description": "Può gestire comunicazioni Polizia e ISTAT"
        },
        {
            "code": "affitti_brevi.channels",
            "name": "Gestione Canali",
            "description": "Può configurare canali di prenotazione"
        },
    ],

    # Frontend routes
    "frontend_routes": [
        {
            "path": "/affitti-brevi/calendario",
            "component": "CalendarioMultiPiattaforma",
            "label": "Calendario",
            "icon": "calendar",
        },
        {
            "path": "/affitti-brevi/prenotazioni",
            "component": "PrenotazioniList",
            "label": "Prenotazioni",
            "icon": "calendar-check",
        },
        {
            "path": "/affitti-brevi/calendari",
            "component": "CalendariList",
            "label": "Calendari iCal",
            "icon": "calendar-alt",
        },
        {
            "path": "/affitti-brevi/tasse",
            "component": "TassaConfigList",
            "label": "Tasse Soggiorno",
            "icon": "euro-sign",
        },
    ],

    # Menu items
    "menu_items": [
        {
            "id": "affitti_brevi.calendario",
            "label": "Calendario",
            "path": "/affitti-brevi/calendario",
            "icon": "calendar",
            "order_index": 5,
            "required_permission": "affitti_brevi.view",
        },
        {
            "id": "affitti_brevi.prenotazioni",
            "label": "Prenotazioni",
            "path": "/affitti-brevi/prenotazioni",
            "icon": "calendar-check",
            "order_index": 10,
            "required_permission": "affitti_brevi.view",
        },
        {
            "id": "affitti_brevi.calendari",
            "label": "Calendari iCal",
            "path": "/affitti-brevi/calendari",
            "icon": "calendar-alt",
            "order_index": 20,
            "required_permission": "affitti_brevi.view",
        },
        {
            "id": "affitti_brevi.tasse",
            "label": "Tasse Soggiorno",
            "path": "/affitti-brevi/tasse",
            "icon": "euro-sign",
            "order_index": 25,
            "required_permission": "affitti_brevi.view",
        },
    ],

    # Dashboard widgets
    "widgets": [
        {
            "id": "affitti_brevi.scadenze",
            "title": "Scadenze Affitti Brevi",
            "component": "ScadenzeWidget",
            "description": "Monitoraggio scadenze urgenti: comunicazioni polizia, ISTAT e adempimenti",
            "default_width": 6,
            "default_height": 4,
            "category": "alerts",
            "module_id": "affitti_brevi",
            "required_permission": "affitti_brevi.view"
        },
        {
            "id": "affitti_brevi.calendario",
            "title": "Calendario Prenotazioni",
            "component": "CalendarioWidget",
            "description": "Panoramica prenotazioni prossimi 7 giorni e conflitti da risolvere",
            "default_width": 6,
            "default_height": 4,
            "category": "stats",
            "module_id": "affitti_brevi",
            "required_permission": "affitti_brevi.view"
        },
    ],

    # Seeds
    "seeds": [
        {
            "name": "seed_canali",
            "description": "Default booking channels (Airbnb, Booking.com, Vrbo, Direct)",
            "target": "tenant"
        }
    ],

    # Documentation
    "documentation": {
        "analysis": "Analisi.md",
        "user_guide": "USER_GUIDE.md",
    },
}
