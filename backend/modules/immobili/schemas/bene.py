"""Common view of a bene (unit or land parcel) for listings and pickers."""
from typing import Optional

from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)
