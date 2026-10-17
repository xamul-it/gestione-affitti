"""
Affitti Brevi Routes

API endpoints for short-term rental management:
- Canali: Booking platform configuration
- Calendari: Property-channel link management
- CalendarioUnificato: Unified calendar view
- Prenotazioni: Booking management
- Soggiorni: Stay operations (check-in, check-out, guests)
- Sync: iCal synchronization
"""
from . import (
    canali,
    calendari,
    calendario_unificato,
    prenotazioni,
    soggiorni,
    sync,
    comunicazioni,
)

# NOTE: router "tasse" ancora assente — la ricostruzione del calcolo/
# dichiarazione tassa di soggiorno contro i modelli attuali (TassaSoggiorno)
# è compito del sotto-progetto B (vedi docs/superpowers/specs/
# 2026-09-28-affitti-brevi-motore-scadenze-compliance-design.md).

__all__ = [
    "canali",
    "calendari",
    "calendario_unificato",
    "prenotazioni",
    "soggiorni",
    "sync",
    "comunicazioni",
]
