from pydantic import BaseModel, EmailStr
from typing import Optional
from ..models import SpecializzazioneTecnico


class TecnicoBase(BaseModel):
    nome: str
    cognome: str
    ragione_sociale: Optional[str] = None
    specializzazione: SpecializzazioneTecnico
    partita_iva: Optional[str] = None
    codice_fiscale: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    indirizzo: Optional[str] = None
    note: Optional[str] = None
    attivo: bool = True


class TecnicoCreate(TecnicoBase):
    pass


class TecnicoUpdate(BaseModel):
    nome: Optional[str] = None
    cognome: Optional[str] = None
    ragione_sociale: Optional[str] = None
    specializzazione: Optional[SpecializzazioneTecnico] = None
    partita_iva: Optional[str] = None
    codice_fiscale: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    indirizzo: Optional[str] = None
    note: Optional[str] = None
    attivo: Optional[bool] = None


class TecnicoResponse(TecnicoBase):
    id: int

    class Config:
        from_attributes = True
