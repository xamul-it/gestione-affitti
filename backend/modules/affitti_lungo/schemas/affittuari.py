from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import date, datetime


class AffittuarioBase(BaseModel):
    nome: Optional[str] = None  # DEPRECATED - use soggetto.nome
    cognome: Optional[str] = None  # DEPRECATED - use soggetto.cognome
    codice_fiscale: str
    data_nascita: Optional[date] = None
    luogo_nascita: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    cellulare: Optional[str] = None
    indirizzo_residenza: Optional[str] = None
    citta_residenza: Optional[str] = None
    cap_residenza: Optional[str] = None
    provincia_residenza: Optional[str] = None
    note: Optional[str] = None


class AffittuarioCreate(AffittuarioBase):
    pass


class AffittuarioUpdate(BaseModel):
    nome: Optional[str] = None
    cognome: Optional[str] = None
    codice_fiscale: Optional[str] = None
    data_nascita: Optional[date] = None
    luogo_nascita: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    cellulare: Optional[str] = None
    indirizzo_residenza: Optional[str] = None
    citta_residenza: Optional[str] = None
    cap_residenza: Optional[str] = None
    provincia_residenza: Optional[str] = None
    note: Optional[str] = None


class AffittuarioResponse(AffittuarioBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
