"""
Core platform schemas for Gestione Affitti.

Pydantic schemas for validation and serialization.

Note: Business-specific schemas have been moved to their respective modules.
"""

from .scadenza import (
    PrioritaScadenza,
    StatoScadenza,
    ScadenzaBase,
    ScadenzaCreate,
    ScadenzaTODOCreate,
    ScadenzaUpdate,
    ScadenzaResponse,
    ScadenzaDestinatarioCreate,
    ScadenzaDestinatarioResponse,
    ScadenzaLogCreate,
    ScadenzaLogResponse,
    ScadenzaListFilters,
    ScadenzaBadgeResponse,
    ScadenzaCompletaRequest,
    ScadenzaPosticipaRequest,
)
from .notifica import (
    CanaleNotifica as CanaleNotificaSchema,
    StatoEmailNotifica as StatoEmailNotificaSchema,
    NotificaResponse,
    NotificaBadgeResponse,
    SegnaTutteLetteResponse,
)
from .documenti import (
    DocumentoBase,
    DocumentoCreate,
    DocumentoUpdate,
    DocumentoResponse,
)

__all__ = [
    "PrioritaScadenza",
    "StatoScadenza",
    "ScadenzaBase",
    "ScadenzaCreate",
    "ScadenzaTODOCreate",
    "ScadenzaUpdate",
    "ScadenzaResponse",
    "ScadenzaDestinatarioCreate",
    "ScadenzaDestinatarioResponse",
    "ScadenzaLogCreate",
    "ScadenzaLogResponse",
    "ScadenzaListFilters",
    "ScadenzaBadgeResponse",
    "ScadenzaCompletaRequest",
    "ScadenzaPosticipaRequest",
    "NotificaResponse",
    "NotificaBadgeResponse",
    "SegnaTutteLetteResponse",
    "DocumentoBase",
    "DocumentoCreate",
    "DocumentoUpdate",
    "DocumentoResponse",
]
