"""
Scadenza Schemas - Pydantic models for deadline tracking using Core System

Combines core.Scadenza fields with affitti_brevi extension metadata.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from datetime import date, datetime

# Import from core
from app.core.platform.models.scadenza import StatoScadenza, PrioritaScadenza

# Import from affitti_brevi extension
from affitti_brevi.models.scadenza_ext import TipoScadenzaAffittiBrevi


class ScadenzaBase(BaseModel):
    """Base schema for deadline (core + extension fields)"""
    # Core fields
    titolo: str = Field(..., max_length=200, description="Titolo della scadenza")
    descrizione: Optional[str] = Field(None, description="Descrizione dettagliata")
    data_scadenza: date = Field(..., description="Data di scadenza (core uses Date, not DateTime)")
    priorita: Optional[PrioritaScadenza] = Field(PrioritaScadenza.MEDIA, description="Priorità della scadenza")

    # Polymorphic association (entity this deadline is linked to)
    entity_type: Optional[str] = Field(None, description="Tipo di entità (es. 'prenotazione', 'report_istat')")
    entity_id: Optional[int] = Field(None, description="ID dell'entità associata")

    # Extension fields (affitti_brevi specific)
    tipo_scadenza: TipoScadenzaAffittiBrevi = Field(..., description="Tipo di scadenza affitti_brevi")


class ScadenzaCreate(ScadenzaBase):
    """Schema for creating a new deadline"""
    # Extension fields for recurrence
    ricorrente: bool = Field(False, description="Scadenza ricorrente")
    frequenza_giorni: Optional[int] = Field(None, ge=1, description="Giorni tra ricorrenze")
    prossima_ricorrenza: Optional[date] = Field(None, description="Prossima ricorrenza")


class ScadenzaUpdate(BaseModel):
    """Schema for updating an existing deadline"""
    # Core fields (optional)
    titolo: Optional[str] = Field(None, max_length=200)
    descrizione: Optional[str] = None
    data_scadenza: Optional[date] = None
    priorita: Optional[PrioritaScadenza] = None
    stato: Optional[StatoScadenza] = None

    # Extension fields (optional)
    tipo_scadenza: Optional[TipoScadenzaAffittiBrevi] = None
    ricorrente: Optional[bool] = None
    frequenza_giorni: Optional[int] = Field(None, ge=1)
    prossima_ricorrenza: Optional[date] = None


class ScadenzaResponse(ScadenzaBase):
    """Schema for API responses (combines core + extension data)"""
    # Core fields
    id: int
    modulo: str  # Always "affitti_brevi" for this module
    stato: StatoScadenza

    # Completion tracking (core pattern)
    creato_da: int
    completato_da: Optional[int] = None
    completato_il: Optional[datetime] = None

    # Timestamps (core)
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Extension fields (recurrence)
    ricorrente: bool
    frequenza_giorni: Optional[int] = None
    prossima_ricorrenza: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class ScadenzaCompletaRequest(BaseModel):
    """Schema for marking deadline as completed"""
    note_completamento: Optional[str] = Field(
        None,
        max_length=500,
        description="Note sul completamento (will be appended to description)"
    )


class ScadenzaBadgeInfo(BaseModel):
    """Schema for badge notification info"""
    count: int = Field(..., description="Numero totale di scadenze attive")
    scadute: int = Field(0, description="Numero di scadenze scadute")
    in_scadenza: int = Field(0, description="Numero di scadenze in scadenza (entro 7 giorni)")
    per_tipo: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="Breakdown per tipo di scadenza"
    )

    model_config = ConfigDict(from_attributes=True)
