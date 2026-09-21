from .affittuari import AffittuarioBase, AffittuarioCreate, AffittuarioUpdate, AffittuarioResponse
from .contratti import ContrattoBase, ContrattoCreate, ContrattoUpdate, ContrattoResponse
from .spese import SpesaBase, SpesaCreate, SpesaUpdate, SpesaResponse
from .incassi import IncassoBase, IncassoCreate, IncassoUpdate, IncassoResponse
from .tecnici import TecnicoBase, TecnicoCreate, TecnicoUpdate, TecnicoResponse
from .documenti import DocumentoBase, DocumentoCreate, DocumentoUpdate, DocumentoResponse

__all__ = [
    # Other entities
    "AffittuarioBase", "AffittuarioCreate", "AffittuarioUpdate", "AffittuarioResponse",
    "ContrattoBase", "ContrattoCreate", "ContrattoUpdate", "ContrattoResponse",
    "SpesaBase", "SpesaCreate", "SpesaUpdate", "SpesaResponse",
    "IncassoBase", "IncassoCreate", "IncassoUpdate", "IncassoResponse",
    "TecnicoBase", "TecnicoCreate", "TecnicoUpdate", "TecnicoResponse",
    "DocumentoBase", "DocumentoCreate", "DocumentoUpdate", "DocumentoResponse",
]
