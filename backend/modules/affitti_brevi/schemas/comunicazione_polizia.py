"""
ComunicazionePolizia Schemas - Pydantic models for police communications
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from ..models.comunicazione_polizia import StatoComunicazione, MetodoInvio


class ComunicazionePoliziaBase(BaseModel):
    """Base schema for police communication"""
    prenotazione_id: int = Field(..., description="ID della prenotazione")


class ComunicazionePoliziaCreate(ComunicazionePoliziaBase):
    """Schema for creating a new police communication"""
    codice_struttura: Optional[str] = Field(None, max_length=50, description="Codice struttura ricettiva")


class ComunicazionePoliziaUpdate(BaseModel):
    """Schema for updating an existing police communication"""
    stato: Optional[StatoComunicazione] = None
    metodo_invio: Optional[MetodoInvio] = None
    codice_struttura: Optional[str] = Field(None, max_length=50)
    dati_ospiti: Optional[Dict[str, Any]] = None
    note: Optional[str] = None


class ComunicazionePoliziaResponse(ComunicazionePoliziaBase):
    """Schema for API responses"""
    id: int
    stato: StatoComunicazione
    metodo_invio: Optional[MetodoInvio] = None
    data_invio: Optional[datetime] = None
    data_conferma: Optional[datetime] = None
    numero_ricevuta: Optional[str] = None
    codice_struttura: Optional[str] = None
    dati_ospiti: Optional[Dict[str, Any]] = None
    errore_messaggio: Optional[str] = None
    tentativi_invio: int
    note: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Computed properties
    is_invio_scaduto: bool
    ore_rimanenti: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ComunicazioneInvioRequest(BaseModel):
    """Schema for marking communication as sent"""
    metodo_invio: MetodoInvio = Field(..., description="Metodo di invio utilizzato")
    numero_ricevuta: Optional[str] = Field(None, max_length=100, description="Numero ricevuta/protocollo")
    codice_struttura: Optional[str] = Field(None, max_length=50, description="Codice struttura")


class ComunicazioneErroreRequest(BaseModel):
    """Schema for marking communication as error"""
    errore_messaggio: str = Field(..., min_length=1, max_length=1000, description="Messaggio di errore")
