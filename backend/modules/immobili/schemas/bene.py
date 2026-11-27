"""Common view of a bene (unit or land parcel) for listings and pickers."""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class PassoPercorso(BaseModel):
    """One ramo on the path from the root down to the bene's ramo."""
    id: int
    nome: str
    tipo: str


class BeneResponse(BaseModel):
    id: int
    tipo_bene: str
    codice: str
    comune: Optional[str] = None
    provincia: Optional[str] = None
    indirizzo: Optional[str] = None
    sezione: Optional[str] = None
    foglio: Optional[str] = None
    particella: Optional[str] = None
    subalterno: Optional[str] = None
    descrizione: Optional[str] = None
    attivo: bool
    raggruppamento_id: Optional[int] = None
    percorso: List[PassoPercorso] = []  # filled on the detail only

    model_config = ConfigDict(from_attributes=True)


class SpostaBene(BaseModel):
    raggruppamento_id: Optional[int] = None
