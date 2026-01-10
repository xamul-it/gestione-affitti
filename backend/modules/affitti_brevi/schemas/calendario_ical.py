"""
CalendarioIcal Schemas - Pydantic models for validation and serialization
"""
from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from typing import Optional
from datetime import datetime
from ..models.calendario_ical import PortaleBooking, StatoSincronizzazione


class CalendarioIcalBase(BaseModel):
    """Base schema with common fields"""
    unita_immobiliare_id: int
    portale: PortaleBooking
    url_ical: str = Field(..., max_length=500)
    url_dashboard_portale: Optional[str] = Field(None, max_length=500)
    attivo: bool = True
    note: Optional[str] = None


class CalendarioIcalCreate(CalendarioIcalBase):
    """Schema for creating a new calendar configuration"""
    pass


class CalendarioIcalUpdate(BaseModel):
    """Schema for updating an existing calendar configuration"""
    unita_immobiliare_id: Optional[int] = None
    portale: Optional[PortaleBooking] = None
    url_ical: Optional[str] = Field(None, max_length=500)
    url_dashboard_portale: Optional[str] = Field(None, max_length=500)
    attivo: Optional[bool] = None
    note: Optional[str] = None


class CalendarioIcalResponse(CalendarioIcalBase):
    """Schema for API responses"""
    id: int
    stato_sincronizzazione: StatoSincronizzazione
    ultima_sincronizzazione: Optional[datetime] = None
    errore_sincronizzazione: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
