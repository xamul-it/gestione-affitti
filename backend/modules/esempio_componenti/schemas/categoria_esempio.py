"""
CategoriaEsempio Schemas - Pydantic validation
"""
from typing import Optional
from pydantic import BaseModel, Field


class CategoriaEsempioBase(BaseModel):
    """Base schema with common fields"""
    codice: str = Field(..., min_length=1, max_length=20, description="Codice univoco")
    nome: str = Field(..., min_length=1, max_length=100, description="Nome categoria")
    descrizione: Optional[str] = Field(None, description="Descrizione opzionale")
    colore: Optional[str] = Field("#3498db", max_length=7, description="Colore esadecimale")
    icona: Optional[str] = Field(None, max_length=50, description="Nome icona")
    ordine: int = Field(0, description="Ordine di visualizzazione")
    attivo: bool = Field(True, description="Se attiva")


class CategoriaEsempioCreate(CategoriaEsempioBase):
    """Schema for creating a new categoria"""
    pass


class CategoriaEsempioUpdate(BaseModel):
    """Schema for updating - all fields optional"""
    codice: Optional[str] = Field(None, min_length=1, max_length=20)
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    descrizione: Optional[str] = None
    colore: Optional[str] = Field(None, max_length=7)
    icona: Optional[str] = Field(None, max_length=50)
    ordine: Optional[int] = None
    attivo: Optional[bool] = None


class CategoriaEsempioResponse(CategoriaEsempioBase):
    """Schema for API responses"""
    id: int

    class Config:
        from_attributes = True
