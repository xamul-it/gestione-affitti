"""
Affitti Brevi Schemas
"""
from .calendario_ical import (
    CalendarioIcalBase,
    CalendarioIcalCreate,
    CalendarioIcalUpdate,
    CalendarioIcalResponse,
)
from .prenotazione import (
    PrenotazioneBase,
    PrenotazioneCreate,
    PrenotazioneUpdate,
    PrenotazioneResponse,
)
from .ospite_prenotazione import (
    OspitePrenotazioneBase,
    OspitePrenotazioneCreate,
    OspitePrenotazioneUpdate,
    OspitePrenotazioneResponse,
)
from .blocco_calendario import (
    BloccoCalendarioBase,
    BloccoCalendarioCreate,
    BloccoCalendarioUpdate,
    BloccoCalendarioResponse,
)
from .tassa_soggiorno import (
    TassaSoggiornoConfigBase,
    TassaSoggiornoConfigCreate,
    TassaSoggiornoConfigUpdate,
    TassaSoggiornoConfigResponse,
    TassaSoggiornoScaglioneBase,
    TassaSoggiornoScaglioneCreate,
    TassaSoggiornoScaglioneUpdate,
    TassaSoggiornoScaglioneResponse,
    TassaSoggiornoConfigWithScaglioni,
)
from .tassa_prenotazione import (
    TassaPrenotazioneBase,
    TassaPrenotazioneCreate,
    TassaPrenotazioneUpdate,
    TassaPrenotazioneResponse,
    TassaCalculationRequest,
    TassaCalculationResponse,
    TassaOverrideRequest,
)
from .scadenza import (
    ScadenzaBase,
    ScadenzaCreate,
    ScadenzaUpdate,
    ScadenzaResponse,
    ScadenzaCompletaRequest,
    ScadenzaBadgeInfo,
)
from .comunicazione_polizia import (
    ComunicazionePoliziaBase,
    ComunicazionePoliziaCreate,
    ComunicazionePoliziaUpdate,
    ComunicazionePoliziaResponse,
    ComunicazioneInvioRequest,
    ComunicazioneErroreRequest,
)

__all__ = [
    "CalendarioIcalBase",
    "CalendarioIcalCreate",
    "CalendarioIcalUpdate",
    "CalendarioIcalResponse",
    "PrenotazioneBase",
    "PrenotazioneCreate",
    "PrenotazioneUpdate",
    "PrenotazioneResponse",
    "OspitePrenotazioneBase",
    "OspitePrenotazioneCreate",
    "OspitePrenotazioneUpdate",
    "OspitePrenotazioneResponse",
    "BloccoCalendarioBase",
    "BloccoCalendarioCreate",
    "BloccoCalendarioUpdate",
    "BloccoCalendarioResponse",
    "TassaSoggiornoConfigBase",
    "TassaSoggiornoConfigCreate",
    "TassaSoggiornoConfigUpdate",
    "TassaSoggiornoConfigResponse",
    "TassaSoggiornoScaglioneBase",
    "TassaSoggiornoScaglioneCreate",
    "TassaSoggiornoScaglioneUpdate",
    "TassaSoggiornoScaglioneResponse",
    "TassaSoggiornoConfigWithScaglioni",
    "TassaPrenotazioneBase",
    "TassaPrenotazioneCreate",
    "TassaPrenotazioneUpdate",
    "TassaPrenotazioneResponse",
    "TassaCalculationRequest",
    "TassaCalculationResponse",
    "TassaOverrideRequest",
    "ScadenzaBase",
    "ScadenzaCreate",
    "ScadenzaUpdate",
    "ScadenzaResponse",
    "ScadenzaCompletaRequest",
    "ScadenzaBadgeInfo",
    "ComunicazionePoliziaBase",
    "ComunicazionePoliziaCreate",
    "ComunicazionePoliziaUpdate",
    "ComunicazionePoliziaResponse",
    "ComunicazioneInvioRequest",
    "ComunicazioneErroreRequest",
]
