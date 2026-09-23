"""
Pydantic schemas for the Immobili module.
"""
from .categoria_catastale import (
    CategoriaCatastaleBase,
    CategoriaCatastaleCreate,
    CategoriaCatastaleUpdate,
    CategoriaCatastale,
)
from .tipologia_terreno import (
    TipologiaTerrenoBase,
    TipologiaTerrenoCreate,
    TipologiaTerrenoUpdate,
    TipologiaTerrenoResponse,
    TipologiaTerrenoSimple,
)
from .terreno import (
    TerrenoBase,
    TerrenoCreate,
    TerrenoUpdate,
    TerrenoResponse,
)
from .immobili import (
    UnitaImmobiliareBase,
    UnitaImmobiliareCreate,
    UnitaImmobiliareUpdate,
    UnitaImmobiliareResponse,
    ImmobileBase,
    ImmobileCreate,
    ImmobileUpdate,
    ImmobileResponse,  # Backward compatibility
)
from .condomini import (
    CondominioBase,
    CondominioCreate,
    CondominioUpdate,
    CondominioResponse,
)
from .proprietari import (
    ProprietarioBase,
    ProprietarioCreate,
    ProprietarioUpdate,
    ProprietarioResponse,
)
from .diritti_immobile import (
    DirittoImmobileBase,
    DirittoImmobileCreate,
    DirittoImmobileUpdate,
    DirittoImmobileResponse,
)
from .certificati_energetici import (
    CertificatoEnergeticoBase,
    CertificatoEnergeticoCreate,
    CertificatoEnergeticoUpdate,
    CertificatoEnergeticoResponse,
)
from .tabelle_millesimali import (
    TabellaMillesimaleBase,
    TabellaMillesimaleCreate,
    TabellaMillesimaleUpdate,
    TabellaMillesimaleResponse,
)
from .millesimi_unita import (
    MillesimiUnitaBase,
    MillesimiUnitaCreate,
    MillesimiUnitaUpdate,
    MillesimiUnitaResponse,
)
from .conduttore import (
    ConduttoreBase,
    ConduttoreCreate,
    ConduttoreUpdate,
    ConduttoreResponse,
)
from .assegnazione_conduttore import (
    AssegnazioneConduttoreBase,
    AssegnazioneConduttoreCreate,
    AssegnazioneConduttoreUpdate,
    AssegnazioneConduttoreResponse,
)
from .spesa_ricorrente import (
    SpesaRicorrenteBase,
    SpesaRicorrenteCreate,
    SpesaRicorrenteUpdate,
    SpesaRicorrenteResponse,
    SegnaPagatoRequest,
    DuplicaSpesaRequest,
)

__all__ = [
    # Categoria Catastale
    "CategoriaCatastaleBase",
    "CategoriaCatastaleCreate",
    "CategoriaCatastaleUpdate",
    "CategoriaCatastale",
    # Tipologia Terreno
    "TipologiaTerrenoBase",
    "TipologiaTerrenoCreate",
    "TipologiaTerrenoUpdate",
    "TipologiaTerrenoResponse",
    "TipologiaTerrenoSimple",
    # Terreno
    "TerrenoBase",
    "TerrenoCreate",
    "TerrenoUpdate",
    "TerrenoResponse",
    # Unità Immobiliari (new naming)
    "UnitaImmobiliareBase", "UnitaImmobiliareCreate", "UnitaImmobiliareUpdate", "UnitaImmobiliareResponse",
    # Backward compatibility
    "ImmobileBase", "ImmobileCreate", "ImmobileUpdate", "ImmobileResponse",
    # Condomini
    "CondominioBase", "CondominioCreate", "CondominioUpdate", "CondominioResponse",
    # Proprietari
    "ProprietarioBase", "ProprietarioCreate", "ProprietarioUpdate", "ProprietarioResponse",
    # Diritti Immobile
    "DirittoImmobileBase", "DirittoImmobileCreate", "DirittoImmobileUpdate", "DirittoImmobileResponse",
    # Certificati Energetici
    "CertificatoEnergeticoBase", "CertificatoEnergeticoCreate", "CertificatoEnergeticoUpdate", "CertificatoEnergeticoResponse",
    # Tabelle Millesimali
    "TabellaMillesimaleBase", "TabellaMillesimaleCreate", "TabellaMillesimaleUpdate", "TabellaMillesimaleResponse",
    # Millesimi Unità
    "MillesimiUnitaBase", "MillesimiUnitaCreate", "MillesimiUnitaUpdate", "MillesimiUnitaResponse",
    # Conduttori
    "ConduttoreBase", "ConduttoreCreate", "ConduttoreUpdate", "ConduttoreResponse",
    # Assegnazioni Conduttore
    "AssegnazioneConduttoreBase", "AssegnazioneConduttoreCreate", "AssegnazioneConduttoreUpdate", "AssegnazioneConduttoreResponse",
    # Spese Ricorrenti
    "SpesaRicorrenteBase", "SpesaRicorrenteCreate", "SpesaRicorrenteUpdate", "SpesaRicorrenteResponse",
    "SegnaPagatoRequest", "DuplicaSpesaRequest",
]
