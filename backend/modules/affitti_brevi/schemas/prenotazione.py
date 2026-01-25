"""
Prenotazione Schemas - Booking Pydantic Models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class PrenotazioneBase(BaseModel):
    """Base schema for booking data"""
    unita_immobiliare_id: int
    data_checkin: date
    data_checkout: date
    numero_ospiti: int = Field(default=1, ge=1)
    codice_prenotazione: str = Field(..., max_length=100)
    codice_conferma: Optional[str] = Field(None, max_length=100)
    nome_ospite_principale: Optional[str] = Field(None, max_length=200)
    email_ospite: Optional[str] = Field(None, max_length=200)
    telefono_ospite: Optional[str] = Field(None, max_length=50)
    prezzo_totale: Optional[Decimal] = None
    prezzo_notte_medio: Optional[Decimal] = None
    valuta: str = Field(default="EUR", max_length=3)
    commissione_canale: Optional[Decimal] = None
    incasso_netto: Optional[Decimal] = None
    note: Optional[str] = None
    note_interne: Optional[str] = None


class PrenotazioneCreate(PrenotazioneBase):
    """Schema for creating a booking manually"""
    calendario_canale_id: Optional[int] = None


class PrenotazioneUpdate(BaseModel):
    """Schema for updating a booking"""
    data_checkin: Optional[date] = None
    data_checkout: Optional[date] = None
    numero_ospiti: Optional[int] = Field(None, ge=1)
    nome_ospite_principale: Optional[str] = Field(None, max_length=200)
    email_ospite: Optional[str] = Field(None, max_length=200)
    telefono_ospite: Optional[str] = Field(None, max_length=50)
    prezzo_totale: Optional[Decimal] = None
    commissione_canale: Optional[Decimal] = None
    incasso_netto: Optional[Decimal] = None
    stato: Optional[str] = None
    note: Optional[str] = None
    note_interne: Optional[str] = None


class PrenotazioneResponse(PrenotazioneBase):
    """Schema for booking response"""
    id: int
    calendario_canale_id: Optional[int] = None
    stato: str
    importata_da_ical: int = 0
    uid_ical: Optional[str] = None
    ultima_modifica_ical: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Computed fields
    notti: int = 0
    canale_codice: str = "SCONOSCIUTO"
    is_attiva: bool = True

    model_config = ConfigDict(from_attributes=True)


class PrenotazioneListResponse(BaseModel):
    """Schema for list of bookings"""
    prenotazioni: List[PrenotazioneResponse]
    totale: int
    skip: int
    limit: int


class PrenotazioneFilterParams(BaseModel):
    """Filter parameters for booking list"""
    unita_immobiliare_id: Optional[int] = None
    canale_id: Optional[int] = None
    data_checkin_da: Optional[date] = None
    data_checkin_a: Optional[date] = None
    stato: Optional[str] = None
    skip: int = 0
    limit: int = 100
