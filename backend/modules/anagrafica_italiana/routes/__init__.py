"""
Routes for anagrafica_italiana module
"""
from .soggetti import router as soggetti_router
from .soggetti_v2 import router as soggetti_v2_router
from .domini import router as domini_router
from .ruoli_azienda import router as ruoli_azienda_router
from .ruoli_azienda_tipi import router as ruoli_azienda_tipi_router
from .documenti import router as documenti_router

__all__ = [
    "soggetti_router",
    "soggetti_v2_router",
    "domini_router",
    "ruoli_azienda_router",
    "ruoli_azienda_tipi_router",
    "documenti_router"
]
