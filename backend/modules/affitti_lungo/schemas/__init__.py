from .immobili import (
    UnitaImmobiliareBase, UnitaImmobiliareCreate, UnitaImmobiliareUpdate, UnitaImmobiliareResponse,
    ImmobileBase, ImmobileCreate, ImmobileUpdate, ImmobileResponse  # Backward compatibility
)
from .affittuari import AffittuarioBase, AffittuarioCreate, AffittuarioUpdate, AffittuarioResponse
from .contratti import ContrattoBase, ContrattoCreate, ContrattoUpdate, ContrattoResponse
from .spese import SpesaBase, SpesaCreate, SpesaUpdate, SpesaResponse
from .incassi import IncassoBase, IncassoCreate, IncassoUpdate, IncassoResponse
from .tecnici import TecnicoBase, TecnicoCreate, TecnicoUpdate, TecnicoResponse
from .certificati_energetici import (
    CertificatoEnergeticoBase,
    CertificatoEnergeticoCreate,
    CertificatoEnergeticoUpdate,
    CertificatoEnergeticoResponse,
)
from .documenti import DocumentoBase, DocumentoCreate, DocumentoUpdate, DocumentoResponse
from .proprietari import ProprietarioBase, ProprietarioCreate, ProprietarioUpdate, ProprietarioResponse
from .diritti_immobile import DirittoImmobileBase, DirittoImmobileCreate, DirittoImmobileUpdate, DirittoImmobileResponse

__all__ = [
    # Unità Immobiliari (new naming)
    "UnitaImmobiliareBase", "UnitaImmobiliareCreate", "UnitaImmobiliareUpdate", "UnitaImmobiliareResponse",
    # Backward compatibility
    "ImmobileBase", "ImmobileCreate", "ImmobileUpdate", "ImmobileResponse",
    # Other entities
    "AffittuarioBase", "AffittuarioCreate", "AffittuarioUpdate", "AffittuarioResponse",
    "ContrattoBase", "ContrattoCreate", "ContrattoUpdate", "ContrattoResponse",
    "SpesaBase", "SpesaCreate", "SpesaUpdate", "SpesaResponse",
    "IncassoBase", "IncassoCreate", "IncassoUpdate", "IncassoResponse",
    "TecnicoBase", "TecnicoCreate", "TecnicoUpdate", "TecnicoResponse",
    "CertificatoEnergeticoBase", "CertificatoEnergeticoCreate", "CertificatoEnergeticoUpdate", "CertificatoEnergeticoResponse",
    "DocumentoBase", "DocumentoCreate", "DocumentoUpdate", "DocumentoResponse",
    "ProprietarioBase", "ProprietarioCreate", "ProprietarioUpdate", "ProprietarioResponse",
    "DirittoImmobileBase", "DirittoImmobileCreate", "DirittoImmobileUpdate", "DirittoImmobileResponse",
]
