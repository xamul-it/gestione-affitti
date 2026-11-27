"""Raggruppamenti (rami) of beni: /api/v1/raggruppamenti."""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from .bene import PassoPercorso


class RaggruppamentoCreate(BaseModel):
    tipo: str
    nome: str
    padre_id: Optional[int] = None
    descrizione: Optional[str] = None
    note: Optional[str] = None


class RaggruppamentoUpdate(BaseModel):
    tipo: Optional[str] = None
    nome: Optional[str] = None
    descrizione: Optional[str] = None
    note: Optional[str] = None
    attivo: Optional[bool] = None


class SpostaRaggruppamento(BaseModel):
    padre_id: Optional[int] = None


class BeneNelRamo(BaseModel):
    id: int
    codice: str
    tipo_bene: str
    descrizione: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RamoBase(BaseModel):
    id: int
    tipo: str
    nome: str
    attivo: bool


class RamoAlbero(RamoBase):
    figli: List["RamoAlbero"] = []
    beni: List[BeneNelRamo] = []


class RamoPiatto(RamoBase):
    percorso: str


class RaggruppamentoDettaglio(RamoBase):
    descrizione: Optional[str] = None
    note: Optional[str] = None
    padre_id: Optional[int] = None
    percorso: List[PassoPercorso]
    figli: List[RamoBase]
    beni: List[BeneNelRamo]


class RaggruppamentoCancellato(BaseModel):
    rami_saliti: int
    beni_saliti: int
