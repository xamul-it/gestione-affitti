"""
Models for Immobili (Real Estate Properties) module.
"""
# Cadastral reference data
from .categoria_catastale import CategoriaCatastale
from .tipo_immobile_categoria_map import TipoImmobileCategoriaMap

# Import ComuneItalia from anagrafica_italiana (moved there as domain data)
import sys
import os
modules_dir = os.path.join(os.path.dirname(__file__), '../../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)
from anagrafica_italiana.models import ComuneItalia

# Property entities
from .unita_immobiliare import UnitaImmobiliare
from .condomini import Condominio
from .proprietari import Proprietario
from .diritti_immobile import DirittoImmobile, TipoDiritto
from .certificati_energetici import CertificatoEnergetico, ClasseEnergetica
from .tabelle_millesimali import TabellaMillesimale, TipoRipartizione
from .millesimi_unita import MillesimiUnita

# Land parcels - domain data in public schema
from .tipologia_terreno import TipologiaTerreno

# Land parcels - tenant override data
from .tipologia_terreno_override import TipologiaTerrenoOverride

# Land parcels - tenant data
from .terreno import Terreno

__all__ = [
    # Cadastral data
    "CategoriaCatastale",
    "ComuneItalia",
    "TipoImmobileCategoriaMap",
    # Property entities
    "UnitaImmobiliare",
    "Condominio",
    "Proprietario",
    "DirittoImmobile",
    "TipoDiritto",
    "CertificatoEnergetico",
    "ClasseEnergetica",
    "TabellaMillesimale",
    "TipoRipartizione",
    "MillesimiUnita",
    # Land parcels
    "Terreno",
    "TipologiaTerreno",
    "TipologiaTerrenoOverride",
]
