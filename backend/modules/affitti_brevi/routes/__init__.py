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
)

# NOTE: router "tasse" ancora assente — la ricostruzione del calcolo/
# dichiarazione tassa di soggiorno contro i modelli attuali (TassaSoggiorno)
# è compito del sotto-progetto B (vedi docs/superpowers/specs/
# 2026-09-28-affitti-brevi-motore-scadenze-compliance-design.md).
#
# NOTE: router "comunicazioni" arriva con il Task 7 di questo piano — non è
# ancora aggiunto qui per evitare un ImportError in ogni verifica intermedia
# (import app.main, test suite) dei Task 2-6, che girano prima che quel
# modulo esista.

__all__ = [
    "canali",
    "calendari",
    "calendario_unificato",
    "prenotazioni",
    "soggiorni",
    "sync",
]
