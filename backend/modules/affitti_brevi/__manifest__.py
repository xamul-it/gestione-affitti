"""
Affitti Brevi Module Manifest
"""

manifest = {
    "name": "Gestione Affitti Brevi",
    "technical_name": "affitti_brevi",
    "version": "1.0.0",
    "status": "production",  # Production ready as of 2025-12-28
    "description": "Sistema completo per la gestione degli affitti brevi con sincronizzazione iCal, calendario multi-piattaforma, gestione ospiti, calcolo tassa di soggiorno e gestione scadenze legali",
    "author": "Gestione Affitti Platform",
    "icon": "calendar",

    "category": "rentals",
    "sequence": 20,

    # Module dependencies
    "dependencies": [
        "immobili",            # For UnitaImmobiliare
        "anagrafica_italiana"  # For SoggettoAnagrafico (guests)
    ],

    # Models provided by this module
    "models": [
        # Phase 1-3: Core booking and calendar models
        "calendario_ical",
        "prenotazione",
        "ospite_prenotazione",
        "blocco_calendario",
        # Phase 4: Tourist tax models
        "tassa_soggiorno_config",
        "tassa_soggiorno_scaglione",
        "tassa_prenotazione",
        # Phase 5: Deadlines and legal compliance models
        # NOTE: Uses core.Scadenza (app.core.platform.models.scadenza) + extension table
        "scadenza_ext",  # Extension table for affitti_brevi-specific scadenza metadata
        "comunicazione_polizia",
    ],

    # API route prefix
    "api_prefix": "/affitti-brevi",

    # Features completed
    "features": {
        "ical_sync": True,           # Phase 2: Automatic iCal synchronization (6-hour interval)
        "multi_calendar": True,      # Phase 3: Multi-platform calendar with conflict detection
        "tourist_tax": True,         # Phase 4: Tourist tax calculation (3 types: fixed, percentage, tiered)
        "deadlines": True,           # Phase 5: Legal deadlines (Police 24h, ISTAT monthly)
        "optimizations": True,       # Phase 6: Database indexes, caching, performance tuning
        "frontend_calendar": True,   # Phase 3: Calendar UI components
        "frontend_tax": True,        # Phase 4: Tax configuration UI
        "frontend_deadlines": True,  # Phase 5: Deadline UI (ScadenzeList, ScadenzaDetail, Badge, ComunicazioniPoliziaList)
    },

    # Performance characteristics (Phase 6 optimizations)
    "performance": {
        "database_indexes": 11,      # Composite indexes for date queries, status filters
        "caching": "in-memory",      # 1-hour TTL on calendar overview
        "recommended_max_properties": 50,  # For optimal calendar performance
        "calendar_cache_ttl": 3600,  # 1 hour
    },

    # Permissions
    "permissions": [
        {
            "code": "affitti_brevi.view",
            "name": "View Short-Term Rentals",
            "description": "Can view bookings, guests, and calendars"
        },
        {
            "code": "affitti_brevi.create",
            "name": "Create Short-Term Rentals",
            "description": "Can create bookings, guests, and calendars"
        },
        {
            "code": "affitti_brevi.edit",
            "name": "Edit Short-Term Rentals",
            "description": "Can modify bookings, guests, and calendars"
        },
        {
            "code": "affitti_brevi.delete",
            "name": "Delete Short-Term Rentals",
            "description": "Can delete bookings, guests, and calendars"
        },
        {
            "code": "affitti_brevi.sync",
            "name": "Sync iCal Calendars",
            "description": "Can trigger manual iCal synchronization"
        },
        {
            "code": "affitti_brevi.tax_config",
            "name": "Configure Tourist Tax",
            "description": "Can configure municipality tourist tax settings"
        },
        {
            "code": "affitti_brevi.tax_override",
            "name": "Override Tax Calculations",
            "description": "Can manually override automatic tax calculations"
        },
        {
            "code": "affitti_brevi.deadlines",
            "name": "Manage Deadlines",
            "description": "Can view and complete legal deadlines (Police, ISTAT)"
        },
        {
            "code": "affitti_brevi.communications",
            "name": "Manage Police Communications",
            "description": "Can manage police guest communications (Alloggiati Web)"
        },
    ],

    # Documentation
    "documentation": {
        "user_guide": "USER_GUIDE.md",           # Comprehensive user manual (Italian)
        "optimization_guide": "OPTIMIZATION_GUIDE.md",  # Performance tuning and deployment guide
        "functional_analysis": "../../docs/ANALISI_FUNZIONALE_AFFITTI_BREVI.md",  # Original requirements
    },
}
