"""
Canale Schemas - Booking Channel Pydantic Models
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CanaleBase(BaseModel):
    """Base schema for channel data"""
    codice: str = Field(..., max_length=50, description="Unique channel code")
    nome: str = Field(..., max_length=100, description="Display name")
    colore: str = Field(default="#808080", max_length=7, description="Hex color")
    simbolo: str = Field(default="?", max_length=5, description="Calendar symbol")
    icona: Optional[str] = Field(None, max_length=50, description="Icon name")
    supporta_ical: bool = Field(default=True, description="Supports iCal import")
    url_pattern_ical: Optional[str] = Field(None, max_length=500)
    attivo: bool = Field(default=True)
    note: Optional[str] = None


class CanaleCreate(CanaleBase):
    """Schema for creating a channel"""
    pass


class CanaleUpdate(BaseModel):
    """Schema for updating a channel"""
    nome: Optional[str] = Field(None, max_length=100)
    colore: Optional[str] = Field(None, max_length=7)
    simbolo: Optional[str] = Field(None, max_length=5)
    icona: Optional[str] = Field(None, max_length=50)
    supporta_ical: Optional[bool] = None
    url_pattern_ical: Optional[str] = Field(None, max_length=500)
    attivo: Optional[bool] = None
    note: Optional[str] = None


class CanaleResponse(CanaleBase):
    """Schema for channel response"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CanaleListResponse(BaseModel):
    """Schema for list of channels"""
    canali: list[CanaleResponse]
    totale: int
    skip: int = 0
    limit: int = 100
