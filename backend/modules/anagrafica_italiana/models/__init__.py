"""
Models for Italian Registry (Anagrafica Italiana) module.
"""
from .soggetto_anagrafico import SoggettoAnagrafico, TipoSoggetto
from .comune_italia import ComuneItalia
from .comune_italia_override import ComuneItaliaOverride
from .ruolo_azienda import RuoloAzienda
from .ruolo_azienda_tipo import RuoloAziendaTipo
from .ruolo_azienda_tipo_override import RuoloAziendaTipoOverride
# Document models moved to app.core.platform.models (core platform service,
# per docs/superpowers/specs/2026-09-14-module-communication-architecture-design.md)
# — re-exported here since anagrafica_italiana's own routes/services import
# them via this package.
from app.core.platform.models import (
    TipoDocumento,
    TipoDocumentoOverride,
    StatoDocumento,
    StatoDocumentoOverride,
    Documento,
    DocumentoFile,
    EntityType,
    TipoDocumentoEnum,
)

__all__ = [
    "SoggettoAnagrafico",
    "TipoSoggetto",
    "ComuneItalia",
    "ComuneItaliaOverride",
    "TipoDocumento",
    "TipoDocumentoOverride",
    "StatoDocumento",
    "StatoDocumentoOverride",
    "RuoloAzienda",
    "RuoloAziendaTipo",
    "RuoloAziendaTipoOverride",
    "Documento",
    "DocumentoFile",
    "EntityType",
    "TipoDocumentoEnum",
]
