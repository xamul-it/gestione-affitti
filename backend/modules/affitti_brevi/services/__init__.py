"""
Affitti Brevi Services

Service layer for short-term rental management:
- CalendarioUnificatoService: Unified calendar view
- ICalSyncService: iCal feed synchronization
- SoggiornoService: Operational stay management
- TassaSoggiornoService: Tourist tax calculation
"""

from .calendario_unificato_service import (
    CalendarioUnificatoService,
    StatoGiornaliero,
    StatoAggregato
)
from .ical_sync_service import ICalSyncService
from .soggiorno_service import SoggiornoService
from .tassa_soggiorno_service import TassaSoggiornoService

__all__ = [
    # Calendar
    "CalendarioUnificatoService",
    "StatoGiornaliero",
    "StatoAggregato",

    # iCal Sync
    "ICalSyncService",

    # Soggiorno
    "SoggiornoService",

    # Tax
    "TassaSoggiornoService",
]
