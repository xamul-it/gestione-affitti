"""
Models for Italian Registry (Anagrafica Italiana) module.
"""
from .soggetto_anagrafico import SoggettoAnagrafico, TipoSoggetto
from .comune_italia import ComuneItalia
from .comune_italia_override import ComuneItaliaOverride
from .tipo_documento import TipoDocumento
from .tipo_documento_override import TipoDocumentoOverride
from .stato_documento import StatoDocumento
from .stato_documento_override import StatoDocumentoOverride
from .ruolo_azienda import RuoloAzienda
from .ruolo_azienda_tipo import RuoloAziendaTipo
from .ruolo_azienda_tipo_override import RuoloAziendaTipoOverride
from .documento import Documento, EntityType, TipoDocumentoEnum
from .documento_file import DocumentoFile

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
