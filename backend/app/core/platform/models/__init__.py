"""
Platform Models

Modelli per le funzionalità platform core.
"""

from .menu import MenuItem
from .dashboard import Widget, UserDashboard
from .scadenza import Scadenza, PrioritaScadenza, StatoScadenza
from .scadenza_destinatario import ScadenzaDestinatario
from .scadenza_log import ScadenzaLog
from .document_job import DocumentJob, JobStatus
from .document_parsing_log import DocumentParsingLog
from .parsing_service_config import ParsingServiceConfig
from .notifica import Notifica, CanaleNotifica, StatoEmailNotifica
from .tipo_documento import TipoDocumento
from .tipo_documento_override import TipoDocumentoOverride
from .stato_documento import StatoDocumento
from .stato_documento_override import StatoDocumentoOverride
from .documento import Documento, EntityType, TipoDocumentoEnum
from .documento_file import DocumentoFile

__all__ = [
    'MenuItem',
    'Widget',
    'UserDashboard',
    'Scadenza',
    'PrioritaScadenza',
    'StatoScadenza',
    'ScadenzaDestinatario',
    'ScadenzaLog',
    'DocumentJob',
    'JobStatus',
    'DocumentParsingLog',
    'ParsingServiceConfig',
    'Notifica',
    'CanaleNotifica',
    'StatoEmailNotifica',
    'TipoDocumento',
    'TipoDocumentoOverride',
    'StatoDocumento',
    'StatoDocumentoOverride',
    'Documento',
    'DocumentoFile',
    'EntityType',
    'TipoDocumentoEnum',
]
