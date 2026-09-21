from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class CondominioBase(BaseModel):
    nome: Optional[str] = None  # Optional - codice is the primary identifier
    codice: str
    indirizzo: str
    citta: str
    cap: Optional[str] = None
    provincia: Optional[str] = None
    codice_fiscale: Optional[str] = None
    partita_iva: Optional[str] = None
    amministratore_nome: Optional[str] = None
    amministratore_telefono: Optional[str] = None
    amministratore_email: Optional[str] = None
    amministratore_indirizzo: Optional[str] = None
    iban: Optional[str] = None
    note: Optional[str] = None
    attivo: bool = True


class CondominioCreate(CondominioBase):
    pass


class CondominioUpdate(BaseModel):
    nome: Optional[str] = None
    codice: Optional[str] = None
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    cap: Optional[str] = None
    provincia: Optional[str] = None
    codice_fiscale: Optional[str] = None
    partita_iva: Optional[str] = None
    amministratore_nome: Optional[str] = None
    amministratore_telefono: Optional[str] = None
    amministratore_email: Optional[str] = None
    amministratore_indirizzo: Optional[str] = None
    iban: Optional[str] = None
    note: Optional[str] = None
    attivo: Optional[bool] = None


class CondominioResponse(CondominioBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
