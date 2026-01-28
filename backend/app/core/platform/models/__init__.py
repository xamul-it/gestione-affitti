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
]
