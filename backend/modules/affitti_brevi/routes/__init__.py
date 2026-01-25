"""
Affitti Brevi Routes

API endpoints for short-term rental management:
- Canali: Booking platform configuration
- Calendari: Property-channel link management
- CalendarioUnificato: Unified calendar view
- Prenotazioni: Booking management
- Soggiorni: Stay operations (check-in, check-out, guests)
- Sync: iCal synchronization
- Tasse: Tourist tax configuration and calculation
"""
from . import (
    canali,
    calendari,
    calendario_unificato,
    prenotazioni,
    soggiorni,
    sync,
    tasse,
)

__all__ = [
    "canali",
    "calendari",
    "calendario_unificato",
    "prenotazioni",
    "soggiorni",
    "sync",
    "tasse",
]
