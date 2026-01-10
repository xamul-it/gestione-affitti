"""
Affitti Brevi Models
"""
from .calendario_ical import CalendarioIcal, PortaleBooking, StatoSincronizzazione
from .prenotazione import Prenotazione, StatoPrenotazione, OriginePrenotazione
from .ospite_prenotazione import OspitePrenotazione
from .blocco_calendario import BloccoCalendario, TipoBlocco, PortaleBlocco
from .tassa_soggiorno_config import TassaSoggiornoConfig, TipoCalcoloTassa
from .tassa_soggiorno_scaglione import TassaSoggiornoScaglione
from .tassa_prenotazione import TassaPrenotazione
from .comunicazione_polizia import ComunicazionePolizia, StatoComunicazione, MetodoInvio

# Use core Scadenza model + extension for affitti_brevi-specific metadata
from app.core.platform.models.scadenza import Scadenza, StatoScadenza, PrioritaScadenza
from .scadenza_ext import ScadenzaAffittiBrevi, TipoScadenzaAffittiBrevi

__all__ = [
    # Models
    "CalendarioIcal",
    "Prenotazione",
    "OspitePrenotazione",
    "BloccoCalendario",
    "TassaSoggiornoConfig",
    "TassaSoggiornoScaglione",
    "TassaPrenotazione",
    "ComunicazionePolizia",
    # Enums
    "PortaleBooking",
    "StatoSincronizzazione",
    "StatoPrenotazione",
    "OriginePrenotazione",
    "TipoBlocco",
    "PortaleBlocco",
    "TipoCalcoloTassa",
    "StatoComunicazione",
    "MetodoInvio",
    # Core models (re-exported for convenience)
    "Scadenza",
    "StatoScadenza",
    "PrioritaScadenza",
    # Extension models
    "ScadenzaAffittiBrevi",
    "TipoScadenzaAffittiBrevi",
]
