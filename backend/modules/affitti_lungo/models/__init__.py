# Import property-related models from immobili module (cross-module dependency)
import sys
import os
# Add modules directory to path for cross-module imports
modules_dir = os.path.join(os.path.dirname(__file__), '../../../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

from immobili.models import (
    UnitaImmobiliare,
    Condominio,
    Proprietario,
    DirittoImmobile,
    TipoDiritto,
    CertificatoEnergetico,
    ClasseEnergetica,
    TabellaMillesimale,
    TipoRipartizione,
    MillesimiUnita,
)

# Import rental-specific models from this module
from .affittuari import Affittuario
from .contratti import Contratto, StatoContratto, UsoImmobile, TipologiaContratto, RegimeFiscale
from .spese import Spesa, CategoriaSpesa
from .incassi import Incasso
from .tecnici import Tecnico, SpecializzazioneTecnico
from .documenti import Documento, EntityType, TipoDocumento
from .ripartizione_spesa import RipartizioneSpesa

__all__ = [
    "UnitaImmobiliare",
    "Affittuario",
    "Contratto",
    "StatoContratto",
    "UsoImmobile",
    "TipologiaContratto",
    "RegimeFiscale",
    "Spesa",
    "CategoriaSpesa",
    "Incasso",
    "Tecnico",
    "SpecializzazioneTecnico",
    "CertificatoEnergetico",
    "ClasseEnergetica",
    "Documento",
    "EntityType",
    "TipoDocumento",
    "Proprietario",
    "DirittoImmobile",
    "TipoDiritto",
    "Condominio",
    "TabellaMillesimale",
    "TipoRipartizione",
    "MillesimiUnita",
    "RipartizioneSpesa",
]
