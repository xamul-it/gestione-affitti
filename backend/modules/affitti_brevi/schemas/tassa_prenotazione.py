"""
TassaPrenotazione Schemas - Pydantic models for calculated tourist tax on bookings
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


class TassaPrenotazioneBase(BaseModel):
    """Base schema for calculated tourist tax"""
    prenotazione_id: int = Field(..., description="ID della prenotazione")
    config_id: int = Field(..., description="ID della configurazione tassa utilizzata")
    importo_totale: Decimal = Field(..., ge=0, description="Importo totale tassa di soggiorno")
    numero_ospiti_tassabili: int = Field(..., ge=0, description="Numero ospiti soggetti a tassa")
    numero_notti_tassabili: int = Field(..., ge=0, description="Numero notti soggette a tassa")


class TassaPrenotazioneCreate(TassaPrenotazioneBase):
    """Schema for creating a new calculated tax (usually automatic)"""
    dettaglio_calcolo: Optional[Dict[str, Any]] = Field(
        None,
        description="Breakdown del calcolo per trasparenza"
    )


class TassaPrenotazioneUpdate(BaseModel):
    """Schema for updating a calculated tax"""
    importo_totale: Optional[Decimal] = Field(None, ge=0)
    numero_ospiti_tassabili: Optional[int] = Field(None, ge=0)
    numero_notti_tassabili: Optional[int] = Field(None, ge=0)
    dettaglio_calcolo: Optional[Dict[str, Any]] = None
    importo_manuale: Optional[Decimal] = Field(None, ge=0, description="Override manuale")
    note_manuale: Optional[str] = Field(None, description="Motivo dell'override")


class TassaPrenotazioneResponse(TassaPrenotazioneBase):
    """Schema for API responses"""
    id: int
    dettaglio_calcolo: Optional[Dict[str, Any]] = None

    # Manual override
    importo_manuale: Optional[Decimal] = None
    note_manuale: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    data_ultimo_calcolo: datetime

    # Computed fields
    importo_finale: Decimal = Field(..., description="Importo finale (manuale se presente, altrimenti calcolato)")
    is_overridden: bool = Field(..., description="True se è stato fatto override manuale")

    model_config = ConfigDict(from_attributes=True)


class TassaCalculationRequest(BaseModel):
    """Schema for requesting tax calculation"""
    prenotazione_id: int = Field(..., description="ID della prenotazione da calcolare")
    force_recalculate: bool = Field(
        False,
        description="Se True, ricalcola anche se esiste già una tassa"
    )


class TassaCalculationResponse(BaseModel):
    """Schema for tax calculation result"""
    tassa: TassaPrenotazioneResponse
    calculation_breakdown: Dict[str, Any] = Field(
        ...,
        description="Dettaglio del calcolo effettuato"
    )
    config_used: Dict[str, Any] = Field(
        ...,
        description="Configurazione utilizzata per il calcolo"
    )


class TassaOverrideRequest(BaseModel):
    """Schema for manual tax override"""
    importo_manuale: Decimal = Field(..., ge=0, description="Nuovo importo manuale")
    note_manuale: str = Field(..., min_length=1, max_length=500, description="Motivo dell'override")
