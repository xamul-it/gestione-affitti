from .immobili import router as immobili_router
from .affittuari import router as affittuari_router
from .contratti import router as contratti_router
from .spese import router as spese_router
from .incassi import router as incassi_router
from .tecnici import router as tecnici_router
from .certificati_energetici import router as certificati_energetici_router
from .documenti import router as documenti_router
from .proprietari import router as proprietari_router
from .diritti_immobile import router as diritti_immobile_router
from .condomini import router as condomini_router
from .tabelle_millesimali import router as tabelle_millesimali_router
from .millesimi_immobile import router as millesimi_immobile_router
from .ripartizione_spesa import router as ripartizione_spesa_router
from .search import router as search_router
from .modules_api import router as modules_api_router

__all__ = [
    "immobili_router",
    "affittuari_router",
    "contratti_router",
    "spese_router",
    "incassi_router",
    "tecnici_router",
    "certificati_energetici_router",
    "documenti_router",
    "proprietari_router",
    "diritti_immobile_router",
    "condomini_router",
    "tabelle_millesimali_router",
    "millesimi_immobile_router",
    "ripartizione_spesa_router",
    "search_router",
    "modules_api_router",
]
