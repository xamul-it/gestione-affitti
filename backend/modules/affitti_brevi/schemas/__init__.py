"""
Affitti Brevi Schemas

Pydantic models for API validation and serialization.
"""

# Canale (Channel)
from .canale import (
    CanaleBase,
    CanaleCreate,
    CanaleUpdate,
    CanaleResponse,
    CanaleListResponse,
)

# Calendario (Calendar view)
from .calendario import (
    CalendarioCanaleBase,
    CalendarioCanaleCreate,
    CalendarioCanaleUpdate,
    CalendarioCanaleResponse,
    CalendarioOverviewRequest,
    CalendarioOverviewResponse,
    RisolviConflittoRequest,
    SyncResult,
    SyncAllResponse,
)

# Prenotazione (Booking)
from .prenotazione import (
    PrenotazioneBase,
    PrenotazioneCreate,
    PrenotazioneUpdate,
    PrenotazioneResponse,
    PrenotazioneListResponse,
    PrenotazioneFilterParams,
)

# Soggiorno (Stay) and Ospiti (Guests)
from .soggiorno import (
    OspiteBase,
    OspiteCreate,
    OspiteUpdate,
    OspiteResponse,
    SoggiornoBase,
    SoggiornoCreate,
    SoggiornoUpdate,
    SoggiornoResponse,
    SoggiornoListResponse,
    SoggiornoFilterParams,
    CheckinRequest,
    VerificaCompletezzaResponse,
    SelfServiceTokenResponse,
)

# Tassa Soggiorno (Tourist Tax)
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

__all__ = [
    # Canale
    "CanaleBase",
    "CanaleCreate",
    "CanaleUpdate",
    "CanaleResponse",
    "CanaleListResponse",

    # Calendario
    "CalendarioCanaleBase",
    "CalendarioCanaleCreate",
    "CalendarioCanaleUpdate",
    "CalendarioCanaleResponse",
    "CalendarioOverviewRequest",
    "CalendarioOverviewResponse",
    "RisolviConflittoRequest",
    "SyncResult",
    "SyncAllResponse",

    # Prenotazione
    "PrenotazioneBase",
    "PrenotazioneCreate",
    "PrenotazioneUpdate",
    "PrenotazioneResponse",
    "PrenotazioneListResponse",
    "PrenotazioneFilterParams",

    # Soggiorno
    "OspiteBase",
    "OspiteCreate",
    "OspiteUpdate",
    "OspiteResponse",
    "SoggiornoBase",
    "SoggiornoCreate",
    "SoggiornoUpdate",
    "SoggiornoResponse",
    "SoggiornoListResponse",
    "SoggiornoFilterParams",
    "CheckinRequest",
    "VerificaCompletezzaResponse",
    "SelfServiceTokenResponse",

    # Tassa Soggiorno
    "TassaSoggiornoConfigBase",
    "TassaSoggiornoConfigCreate",
    "TassaSoggiornoConfigUpdate",
    "TassaSoggiornoConfigResponse",
    "TassaSoggiornoScaglioneBase",
    "TassaSoggiornoScaglioneCreate",
    "TassaSoggiornoScaglioneUpdate",
    "TassaSoggiornoScaglioneResponse",
    "TassaSoggiornoConfigWithScaglioni",
]
