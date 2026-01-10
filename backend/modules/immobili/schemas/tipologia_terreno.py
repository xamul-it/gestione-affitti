"""
Pydantic schemas for TipologiaTerreno (Land Type).

Domain data stored in public schema.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TipologiaTerrenoBase(BaseModel):
    """Base schema for land type classification."""
    codice: str = Field(..., max_length=10, description="Code (e.g., AGR, EDI)")
    nome: str = Field(..., max_length=100, description="Full name")
    descrizione: Optional[str] = Field(None, description="Detailed description")
    ordinamento: int = Field(default=0, description="Sort order for UI")
    attiva: bool = Field(default=True, description="Active flag")


class TipologiaTerrenoCreate(TipologiaTerrenoBase):
    """Schema for creating a new tipologia terreno (tenant-specific)."""
    pass


class TipologiaTerrenoUpdate(BaseModel):
    """Schema for updating. All fields optional."""
    codice: Optional[str] = Field(None, max_length=10)
    nome: Optional[str] = Field(None, max_length=100)
    descrizione: Optional[str] = None
    ordinamento: Optional[int] = None
    attiva: Optional[bool] = None


class TipologiaTerrenoResponse(TipologiaTerrenoBase):
    """Schema for tipologia terreno response."""
    id: int
    tenant_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TipologiaTerrenoSimple(BaseModel):
    """Simplified schema for embedding in responses."""
    id: int
    codice: str
    nome: str

    class Config:
        from_attributes = True
