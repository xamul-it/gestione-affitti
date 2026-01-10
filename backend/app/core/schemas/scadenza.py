"""
Pydantic Schemas for Scadenzario (Universal Deadline/Reminder System)

Validation and serialization schemas for Scadenza, ScadenzaDestinatario, and ScadenzaLog.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class PrioritaScadenza(str, Enum):
    """Priority levels for scadenze"""
    BASSA = "BASSA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"


class StatoScadenza(str, Enum):
    """Lifecycle states for scadenze"""
    ATTIVA = "ATTIVA"
    SCADUTA = "SCADUTA"
    COMPLETATA = "COMPLETATA"
    POSTICIPATA = "POSTICIPATA"
    CANCELLATA = "CANCELLATA"


# =============================================================================
# SCADENZA SCHEMAS
# =============================================================================

class ScadenzaBase(BaseModel):
    """Base schema with common fields"""
    modulo: Optional[str] = Field(None, max_length=100, description="Module name (null for TODO)")
    entity_type: Optional[str] = Field(None, max_length=100, description="Entity type (null for TODO)")
    entity_id: Optional[int] = Field(None, description="Entity ID (null for TODO)")
    titolo: str = Field(..., max_length=200, min_length=1, description="Short title/summary")
    descrizione: Optional[str] = Field(None, description="Detailed description/notes")
    data_scadenza: date = Field(..., description="Due date")
    priorita: PrioritaScadenza = Field(PrioritaScadenza.MEDIA, description="Priority level")

    @validator('titolo')
    def titolo_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('titolo cannot be empty')
        return v.strip()

    @validator('data_scadenza')
    def data_scadenza_not_past(cls, v):
        """Warn if creating a scadenza with past date, but allow it"""
        if v < date.today():
            # Don't raise error, just allow it (user might be creating overdue items)
            pass
        return v


class ScadenzaCreate(ScadenzaBase):
    """Schema for creating a new scadenza"""
    destinatari_ids: Optional[List[int]] = Field(
        default_factory=list,
        description="List of user IDs to notify (empty = notify only creator)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "modulo": "affitti_lungo",
                "entity_type": "contratto",
                "entity_id": 123,
                "titolo": "Rinnovo contratto di locazione",
                "descrizione": "Inviare raccomandata 60 giorni prima della scadenza",
                "data_scadenza": "2025-03-15",
                "priorita": "ALTA",
                "destinatari_ids": [5, 8, 12]
            }
        }


class ScadenzaTODOCreate(BaseModel):
    """Simplified schema for creating standalone TODOs"""
    titolo: str = Field(..., max_length=200, min_length=1)
    descrizione: Optional[str] = None
    data_scadenza: date
    priorita: PrioritaScadenza = PrioritaScadenza.MEDIA
    destinatari_ids: Optional[List[int]] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "titolo": "Chiamare idraulico per riparazione",
                "descrizione": "Perdita acqua in cucina appartamento 3B",
                "data_scadenza": "2025-12-15",
                "priorita": "ALTA"
            }
        }


class ScadenzaUpdate(BaseModel):
    """Schema for updating an existing scadenza (all fields optional)"""
    titolo: Optional[str] = Field(None, max_length=200, min_length=1)
    descrizione: Optional[str] = None
    data_scadenza: Optional[date] = None
    priorita: Optional[PrioritaScadenza] = None
    stato: Optional[StatoScadenza] = None
    destinatari_ids: Optional[List[int]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "data_scadenza": "2025-04-15",
                "priorita": "MEDIA",
                "stato": "POSTICIPATA"
            }
        }


class ScadenzaResponse(ScadenzaBase):
    """Schema for API responses"""
    id: int
    stato: StatoScadenza
    creato_da: int
    creato_il: datetime
    modificato_il: Optional[datetime] = None
    completato_da: Optional[int] = None
    completato_il: Optional[datetime] = None
    is_todo: bool = Field(..., description="True if standalone TODO")
    is_scaduta: bool = Field(..., description="True if past due and not completed")

    # Nested relationships (optional - can be loaded separately)
    destinatari: Optional[List['ScadenzaDestinatarioResponse']] = None
    logs: Optional[List['ScadenzaLogResponse']] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "modulo": "affitti_lungo",
                "entity_type": "contratto",
                "entity_id": 123,
                "titolo": "Rinnovo contratto di locazione",
                "descrizione": "Inviare raccomandata 60 giorni prima della scadenza",
                "data_scadenza": "2025-03-15",
                "priorita": "ALTA",
                "stato": "ATTIVA",
                "creato_da": 1,
                "creato_il": "2025-01-15T10:30:00",
                "modificato_il": None,
                "completato_da": None,
                "completato_il": None,
                "is_todo": False,
                "is_scaduta": False
            }
        }


# =============================================================================
# SCADENZA DESTINATARIO SCHEMAS
# =============================================================================

class ScadenzaDestinatarioCreate(BaseModel):
    """Schema for adding a recipient to a scadenza"""
    scadenza_id: int
    user_id: int


class ScadenzaDestinatarioResponse(BaseModel):
    """Schema for API responses"""
    id: int
    scadenza_id: int
    user_id: int
    notificato: bool
    notificato_il: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# SCADENZA LOG SCHEMAS
# =============================================================================

class ScadenzaLogCreate(BaseModel):
    """Schema for creating a log entry (usually internal)"""
    scadenza_id: int
    user_id: Optional[int] = None
    azione: str = Field(..., max_length=50)
    campo_modificato: Optional[str] = Field(None, max_length=100)
    valore_precedente: Optional[str] = None
    valore_nuovo: Optional[str] = None
    note: Optional[str] = None


class ScadenzaLogResponse(BaseModel):
    """Schema for API responses"""
    id: int
    scadenza_id: int
    user_id: Optional[int] = None
    timestamp: datetime
    azione: str
    campo_modificato: Optional[str] = None
    valore_precedente: Optional[str] = None
    valore_nuovo: Optional[str] = None
    note: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "scadenza_id": 1,
                "user_id": 5,
                "timestamp": "2025-01-15T10:30:00",
                "azione": "CREATA",
                "campo_modificato": None,
                "valore_precedente": None,
                "valore_nuovo": None,
                "note": "Scadenza creata per rinnovo contratto"
            }
        }


# =============================================================================
# BATCH AND FILTER SCHEMAS
# =============================================================================

class ScadenzaListFilters(BaseModel):
    """Filters for listing scadenze"""
    modulo: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    stato: Optional[StatoScadenza] = None
    priorita: Optional[PrioritaScadenza] = None
    creato_da: Optional[int] = None
    solo_todo: Optional[bool] = Field(None, description="Filter only standalone TODOs")
    solo_scadute: Optional[bool] = Field(None, description="Filter only overdue")
    data_da: Optional[date] = Field(None, description="Filter by date range start")
    data_a: Optional[date] = Field(None, description="Filter by date range end")


class ScadenzaBadgeResponse(BaseModel):
    """Badge info for UI display"""
    count_attive: int = Field(..., description="Active scadenze count")
    count_scadute: int = Field(..., description="Overdue scadenze count")
    count_alta_priorita: int = Field(..., description="High priority count")
    color: str = Field(..., description="Badge color: red/yellow/green")
    tooltip: str = Field(..., description="Tooltip text for user")

    class Config:
        json_schema_extra = {
            "example": {
                "count_attive": 5,
                "count_scadute": 2,
                "count_alta_priorita": 1,
                "color": "red",
                "tooltip": "2 scadenze scadute, 1 ad alta priorità"
            }
        }


class ScadenzaCompletaRequest(BaseModel):
    """Request to mark scadenza as completed"""
    note: Optional[str] = Field(None, description="Optional completion notes")


class ScadenzaPosticipaRequest(BaseModel):
    """Request to postpone scadenza to new date"""
    nuova_data: date = Field(..., description="New due date")
    note: Optional[str] = Field(None, description="Reason for postponement")

    @validator('nuova_data')
    def nuova_data_future(cls, v):
        if v <= date.today():
            raise ValueError('nuova_data must be in the future')
        return v


# Update forward references for nested relationships
ScadenzaResponse.model_rebuild()
