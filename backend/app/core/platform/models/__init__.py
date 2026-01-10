"""
Platform Models

Modelli per le funzionalità platform core.
"""

from .menu import MenuItem
from .dashboard import Widget, UserDashboard
from .scadenza import Scadenza, PrioritaScadenza, StatoScadenza
from .scadenza_destinatario import ScadenzaDestinatario
from .scadenza_log import ScadenzaLog

__all__ = [
    'MenuItem',
    'Widget',
    'UserDashboard',
    'Scadenza',
    'PrioritaScadenza',
    'StatoScadenza',
    'ScadenzaDestinatario',
    'ScadenzaLog',
]
