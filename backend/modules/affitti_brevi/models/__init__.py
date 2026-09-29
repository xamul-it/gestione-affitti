"""
Affitti Brevi Models

Complete model set for short-term rental management:
- Canale: Booking platform configuration
- CalendarioCanale: Property-channel link with iCal sync
- Prenotazione: Booking from channel
- Soggiorno: Operational stay
- OspiteSoggiorno: Guest data
- TassaSoggiornoConfig/Scaglione: Tax configuration
- TassaSoggiorno: Calculated tax per stay
- Comunicazione: Mandatory communications (Police, ISTAT)
- BloccoCalendario: Manual calendar blocks
"""

# Channel configuration
from .canale import Canale, DEFAULT_CANALI

# Property-channel link
from .calendario_canale import CalendarioCanale, StatoSincronizzazione
CalendarioIcal = CalendarioCanale  # backward-compat alias

# Bookings from channels
from .prenotazione import Prenotazione, StatoPrenotazione

# Operational stay
from .soggiorno import Soggiorno, StatoSoggiorno, StatoCompliance

# Guests
from .ospite_soggiorno import OspiteSoggiorno, RuoloOspite, StatoDocumento

# Tourist tax
from .tassa_soggiorno_config import TassaSoggiornoConfig, TipoCalcoloTassa
from .tassa_soggiorno_scaglione import TassaSoggiornoScaglione
from .tassa_soggiorno import TassaSoggiorno, StatoPagamentoTassa

# Communications
from .comunicazione import (
    Comunicazione,
    TipoComunicazione,
    StatoComunicazione,
    MetodoInvio
)

# Calendar blocks
from .blocco_calendario import BloccoCalendario, TipoBlocco

__all__ = [
    # Channel
    "Canale",
    "DEFAULT_CANALI",

    # Calendar-Channel
    "CalendarioCanale",
    "CalendarioIcal",  # backward-compat alias for CalendarioCanale
    "StatoSincronizzazione",

    # Prenotazione
    "Prenotazione",
    "StatoPrenotazione",

    # Soggiorno
    "Soggiorno",
    "StatoSoggiorno",
    "StatoCompliance",

    # Ospiti
    "OspiteSoggiorno",
    "RuoloOspite",
    "StatoDocumento",

    # Tassa
    "TassaSoggiornoConfig",
    "TipoCalcoloTassa",
    "TassaSoggiornoScaglione",
    "TassaSoggiorno",
    "StatoPagamentoTassa",

    # Comunicazioni
    "Comunicazione",
    "TipoComunicazione",
    "StatoComunicazione",
    "MetodoInvio",

    # Blocchi
    "BloccoCalendario",
    "TipoBlocco",
]
