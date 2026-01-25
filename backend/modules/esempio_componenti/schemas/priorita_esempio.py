"""
PrioritaEsempio Schemas - Pydantic validation
"""
from typing import Optional
from pydantic import BaseModel, Field


class PrioritaEsempioBase(BaseModel):
    """Base schema with common fields"""
    codice: str = Field(..., min_length=1, max_length=10, description="Codice univoco")
    nome: str = Field(..., min_length=1, max_length=50, description="Nome priorità")
    livello: int = Field(0, ge=0, description="Livello numerico (più alto = più urgente)")
    colore: Optional[str] = Field("#95a5a6", max_length=7, description="Colore esadecimale")
    attivo: bool = Field(True, description="Se attiva")


class PrioritaEsempioCreate(PrioritaEsempioBase):
    """Schema for creating a new priorità"""
    pass


class PrioritaEsempioUpdate(BaseModel):
    """Schema for updating - all fields optional"""
    codice: Optional[str] = Field(None, min_length=1, max_length=10)
    nome: Optional[str] = Field(None, min_length=1, max_length=50)
    livello: Optional[int] = Field(None, ge=0)
    colore: Optional[str] = Field(None, max_length=7)
    attivo: Optional[bool] = None


class PrioritaEsempioResponse(PrioritaEsempioBase):
    """Schema for API responses"""
    id: int

    class Config:
        from_attributes = True
