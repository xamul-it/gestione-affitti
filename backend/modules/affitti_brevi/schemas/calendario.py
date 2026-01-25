"""
Calendario Schemas - Calendar View Pydantic Models
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import date, datetime


class CalendarioCanaleBase(BaseModel):
    """Base schema for calendar-channel configuration"""
    unita_immobiliare_id: int
    canale_id: int
    codice_esterno: Optional[str] = Field(None, max_length=100)
    url_annuncio: Optional[str] = Field(None, max_length=500)
    url_ical: Optional[str] = Field(None, max_length=500)
    url_ical_export: Optional[str] = Field(None, max_length=500)
    sync_attiva: bool = Field(default=True)
    intervallo_sync_ore: int = Field(default=6, ge=1, le=168)
    attivo: bool = Field(default=True)
    note: Optional[str] = None


class CalendarioCanaleCreate(CalendarioCanaleBase):
    """Schema for creating calendar-channel link"""
    pass


class CalendarioCanaleUpdate(BaseModel):
    """Schema for updating calendar-channel link"""
    codice_esterno: Optional[str] = Field(None, max_length=100)
    url_annuncio: Optional[str] = Field(None, max_length=500)
    url_ical: Optional[str] = Field(None, max_length=500)
    url_ical_export: Optional[str] = Field(None, max_length=500)
    sync_attiva: Optional[bool] = None
    intervallo_sync_ore: Optional[int] = Field(None, ge=1, le=168)
    attivo: Optional[bool] = None
    note: Optional[str] = None


class CalendarioCanaleResponse(CalendarioCanaleBase):
    """Schema for calendar-channel response"""
    id: int
    stato_sincronizzazione: str
    ultima_sincronizzazione: Optional[datetime] = None
    errore_sincronizzazione: Optional[str] = None
    prenotazioni_importate: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Unified Calendar View Schemas

class StatoCanaleGiorno(BaseModel):
    """Status of a channel for a specific day"""
    stato: str = Field(..., description="LIBERO, PRENOTATO, CHIUSO")
    colore: str
    simbolo: str
    prenotazione: Optional[Dict] = None


class GiornoCalendario(BaseModel):
    """Calendar day data"""
    data: str
    canali: Dict[str, StatoCanaleGiorno]
    stato_aggregato: str = Field(..., description="LIBERO, OCCUPATO, NON_DISPONIBILE, CONFLITTO")
    prenotazioni: List[Dict] = []
    richiede_azione: bool = False


class ProprietaCalendario(BaseModel):
    """Property calendar data"""
    unita_immobiliare_id: int
    nome: str
    canali_attivi: List[Dict]
    giorni: Dict[str, GiornoCalendario]


class LegendaCalendario(BaseModel):
    """Calendar legend"""
    canali: List[Dict]
    stati: Dict[str, Dict]
    stati_aggregati: Dict[str, Dict]


class ConflittoCalendario(BaseModel):
    """Calendar conflict"""
    unita_immobiliare_id: int
    data: str
    prenotazioni: List[Dict]


class CalendarioOverviewResponse(BaseModel):
    """Full calendar overview response"""
    periodo: Dict[str, Any]
    legenda: LegendaCalendario
    proprieta: List[ProprietaCalendario]
    conflitti: Dict[str, Any]


class CalendarioOverviewRequest(BaseModel):
    """Request for calendar overview"""
    data_inizio: date
    data_fine: date
    unita_immobiliare_ids: Optional[List[int]] = None
    include_dettagli: bool = True


class RisolviConflittoRequest(BaseModel):
    """Request to resolve a conflict"""
    prenotazione_id_da_mantenere: int
    prenotazione_id_da_cancellare: int


class SyncResult(BaseModel):
    """iCal sync result"""
    calendario_id: int
    canale: str
    create: int
    aggiornate: int
    saltate: int
    errore: Optional[str] = None


class SyncAllResponse(BaseModel):
    """Response from sync all"""
    calendari_processati: int
    prenotazioni_create: int
    prenotazioni_aggiornate: int
    prenotazioni_saltate: int
    errori: int
    dettagli: List[SyncResult]
