# Import models FIRST to ensure they're registered with SQLAlchemy Base
# before routes and other components are loaded.
from . import models


def get_routers():
    """
    Lazily import routers to avoid circular imports at module import time.
    """
    from .routes.caselle import router as caselle_router
    from .routes.messaggi import router as messaggi_router
    from .routes.risposte import router as risposte_router
    from .routes.scheduler import router as scheduler_router
    from .routes.audit import router as audit_router

    return [caselle_router, messaggi_router, risposte_router, scheduler_router, audit_router]


def register_module(app) -> None:
    """
    Hook chiamato dalla piattaforma dopo la registrazione del modulo.

    Avvia il polling scheduler PEC in background.
    Il controllo su _started evita doppie attivazioni (es. hot-reload uvicorn).
    """
    import logging as _logging
    _logger = _logging.getLogger(__name__)

    try:
        from .services.polling_scheduler import get_scheduler
        scheduler = get_scheduler()
        if not scheduler._started:
            scheduler.start()
            _logger.info("[gestione_pec] Polling scheduler avviato")
        else:
            _logger.debug("[gestione_pec] Polling scheduler già attivo, skip")
    except Exception as exc:
        _logger.error("[gestione_pec] Impossibile avviare polling scheduler: %s", exc, exc_info=True)


# Routers provided by this module (lazy — populated by get_routers())
ROUTERS = []

__all__ = [
    "models",
    "ROUTERS",
    "get_routers",
    "register_module",
]
