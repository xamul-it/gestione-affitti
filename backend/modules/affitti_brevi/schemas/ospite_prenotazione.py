"""
OspitePrenotazione Schemas - Pydantic models for validation and serialization
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date, datetime


class OspitePrenotazioneBase(BaseModel):
    """Base schema with common fields"""
    prenotazione_id: int
    soggetto_anagrafico_id: int
    ospite_principale: bool = False
    documento_identita_caricato: bool = False
    tipo_documento: Optional[str] = Field(None, max_length=50)
    numero_documento: Optional[str] = Field(None, max_length=50)
    data_scadenza_documento: Optional[date] = None
    note: Optional[str] = None


class OspitePrenotazioneCreate(OspitePrenotazioneBase):
    """Schema for creating a new guest-booking link"""
    pass


class OspitePrenotazioneUpdate(BaseModel):
    """Schema for updating an existing guest-booking link"""
    prenotazione_id: Optional[int] = None
    soggetto_anagrafico_id: Optional[int] = None
    ospite_principale: Optional[bool] = None
    documento_identita_caricato: Optional[bool] = None
    tipo_documento: Optional[str] = Field(None, max_length=50)
    numero_documento: Optional[str] = Field(None, max_length=50)
    data_scadenza_documento: Optional[date] = None
    note: Optional[str] = None


class OspitePrenotazioneResponse(OspitePrenotazioneBase):
    """Schema for API responses"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
