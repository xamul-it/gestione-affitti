"""
BloccoCalendario Schemas - Pydantic models for validation and serialization
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date, datetime
from ..models.blocco_calendario import TipoBlocco, PortaleBlocco


class BloccoCalendarioBase(BaseModel):
    """Base schema with common fields"""
    immobile_id: int
    portale: PortaleBlocco
    data_inizio: date
    data_fine: date
    tipo_blocco: TipoBlocco
    motivo: Optional[str] = None
    note: Optional[str] = None


class BloccoCalendarioCreate(BloccoCalendarioBase):
    """Schema for creating a new calendar block"""
    pass


class BloccoCalendarioUpdate(BaseModel):
    """Schema for updating an existing calendar block"""
    immobile_id: Optional[int] = None
    portale: Optional[PortaleBlocco] = None
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    tipo_blocco: Optional[TipoBlocco] = None
    motivo: Optional[str] = None
    note: Optional[str] = None


class BloccoCalendarioResponse(BloccoCalendarioBase):
    """Schema for API responses"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Computed field
    giorni_bloccati: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
