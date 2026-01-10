"""
Prenotazione Schemas - Pydantic models for validation and serialization
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from ..models.prenotazione import StatoPrenotazione, OriginePrenotazione


class PrenotazioneBase(BaseModel):
    """Base schema with common fields"""
    unita_immobiliare_id: int
    calendario_ical_id: Optional[int] = None
    codice_prenotazione: str = Field(..., max_length=100)
    portale_origine: OriginePrenotazione
    data_checkin: date
    data_checkout: date
    numero_ospiti: int = Field(default=1, ge=1, le=50)
    prezzo_totale: Optional[Decimal] = Field(None, ge=0)
    valuta: str = Field(default="EUR", max_length=3)
    prezzo_manuale: Optional[Decimal] = Field(None, ge=0)
    stato: StatoPrenotazione = StatoPrenotazione.CONFERMATA
    note: Optional[str] = None


class PrenotazioneCreate(PrenotazioneBase):
    """Schema for creating a new booking"""
    pass


class PrenotazioneUpdate(BaseModel):
    """Schema for updating an existing booking"""
    unita_immobiliare_id: Optional[int] = None
    calendario_ical_id: Optional[int] = None
    codice_prenotazione: Optional[str] = Field(None, max_length=100)
    portale_origine: Optional[OriginePrenotazione] = None
    data_checkin: Optional[date] = None
    data_checkout: Optional[date] = None
    numero_ospiti: Optional[int] = Field(None, ge=1, le=50)
    prezzo_totale: Optional[Decimal] = Field(None, ge=0)
    valuta: Optional[str] = Field(None, max_length=3)
    prezzo_manuale: Optional[Decimal] = Field(None, ge=0)
    stato: Optional[StatoPrenotazione] = None
    note: Optional[str] = None


class PrenotazioneResponse(PrenotazioneBase):
    """Schema for API responses"""
    id: int
    importata_da_ical: int
    ultima_modifica_ical: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Computed fields
    notti: Optional[int] = None
    prezzo_notte: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)
