"""
Routes for immobili module
"""
from .categorie_catastali import router as categorie_catastali_router
from .terreni import router as terreni_router
from .tipologie_terreno import router as tipologie_terreno_router
from .immobili import router as immobili_router
from .condomini import router as condomini_router
from .proprietari import router as proprietari_router
from .diritti_immobile import router as diritti_immobile_router
from .certificati_energetici import router as certificati_energetici_router
from .tabelle_millesimali import router as tabelle_millesimali_router
from .millesimi_immobile import router as millesimi_immobile_router
from .conduttori import router as conduttori_router
from .assegnazioni_conduttore import router as assegnazioni_conduttore_router
from .spese_ricorrenti import router as spese_ricorrenti_router

__all__ = [
    "categorie_catastali_router",
    "terreni_router",
    "tipologie_terreno_router",
    "immobili_router",
    "condomini_router",
    "proprietari_router",
    "diritti_immobile_router",
    "certificati_energetici_router",
    "tabelle_millesimali_router",
    "millesimi_immobile_router",
    "conduttori_router",
    "assegnazioni_conduttore_router",
    "spese_ricorrenti_router",
]
