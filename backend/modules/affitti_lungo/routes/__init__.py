from .affittuari import router as affittuari_router
from .contratti import router as contratti_router
from .spese import router as spese_router
from .incassi import router as incassi_router
from .tecnici import router as tecnici_router
from .documenti import router as documenti_router
from .ripartizione_spesa import router as ripartizione_spesa_router
from .search import router as search_router
from .modules_api import router as modules_api_router

__all__ = [
    "affittuari_router",
    "contratti_router",
    "spese_router",
    "incassi_router",
    "tecnici_router",
    "documenti_router",
    "ripartizione_spesa_router",
    "search_router",
    "modules_api_router",
]
