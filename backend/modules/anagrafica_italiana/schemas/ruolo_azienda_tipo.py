"""
Pydantic schemas for RuoloAziendaTipo (Company Role Types)
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class RuoloAziendaTipoBase(BaseModel):
    """Base schema for ruolo azienda tipo"""
    nome: str = Field(..., min_length=1, max_length=100, description="Nome del ruolo (es: 'Amministratore Delegato')")
    descrizione: Optional[str] = Field(None, max_length=500, description="Descrizione opzionale del ruolo")
    attivo: bool = Field(True, description="Se False, il ruolo non appare più nell'autocomplete")


class RuoloAziendaTipoCreate(RuoloAziendaTipoBase):
    """Schema for creating a new ruolo tipo"""
    pass


class RuoloAziendaTipoUpdate(BaseModel):
    """Schema for updating a ruolo tipo"""
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    descrizione: Optional[str] = Field(None, max_length=500)
    attivo: Optional[bool] = None


class RuoloAziendaTipoResponse(RuoloAziendaTipoBase):
    """Schema for ruolo tipo response"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RuoloAziendaTipoMerge(BaseModel):
    """Schema for merging two ruolo types"""
    source_id: int = Field(..., description="ID del ruolo da eliminare (es: 'segretaria')")
    target_id: int = Field(..., description="ID del ruolo di destinazione (es: 'Segretaria')")

    class Config:
        json_schema_extra = {
            "example": {
                "source_id": 2,
                "target_id": 1,
            }
        }
