from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProprietarioBase(BaseModel):
    nome: Optional[str] = Field(None, max_length=100)  # DEPRECATED - use soggetto.nome
    cognome: Optional[str] = Field(None, max_length=100)  # DEPRECATED - use soggetto.cognome
    codice_fiscale: Optional[str] = Field(None, max_length=16, min_length=16)
    data_nascita: Optional[str] = None
    luogo_nascita: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    telefono: Optional[str] = Field(None, max_length=20)
    cellulare: Optional[str] = Field(None, max_length=20)
    indirizzo: Optional[str] = Field(None, max_length=255)
    citta: Optional[str] = Field(None, max_length=100)
    cap: Optional[str] = Field(None, max_length=10)
    provincia: Optional[str] = Field(None, max_length=2)
    note: Optional[str] = Field(None, max_length=500)
    attivo: Optional[bool] = None


class ProprietarioCreate(ProprietarioBase):
    pass


class ProprietarioUpdate(ProprietarioBase):
    pass


class ProprietarioResponse(ProprietarioBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
