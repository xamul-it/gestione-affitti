"""
ElementoEsempio Schemas - Pydantic validation
"""
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, condecimal
from enum import Enum


class StatoElemento(str, Enum):
    """Possible states for an elemento"""
    BOZZA = "bozza"
    ATTIVO = "attivo"
    COMPLETATO = "completato"
    ANNULLATO = "annullato"


class ElementoEsempioBase(BaseModel):
    """Base schema with common fields"""
    codice: str = Field(..., min_length=1, max_length=20, description="Codice identificativo")
    titolo: str = Field(..., min_length=1, max_length=200, description="Titolo elemento")
    descrizione: Optional[str] = Field(None, description="Descrizione estesa")

    # Relationships
    categoria_id: Optional[int] = Field(None, description="FK categoria")
    priorita_id: Optional[int] = Field(None, description="FK priorità")

    # Numeric fields
    quantita: Optional[int] = Field(1, ge=0, description="Quantità")
    importo: Optional[condecimal(max_digits=10, decimal_places=2)] = Field(None, ge=0, description="Importo")
    percentuale: Optional[condecimal(max_digits=5, decimal_places=2)] = Field(None, ge=0, le=100, description="Percentuale")

    # Date fields
    data_inizio: Optional[date] = Field(None, description="Data inizio")
    data_fine: Optional[date] = Field(None, description="Data fine")

    # Status fields
    stato: StatoElemento = Field(StatoElemento.BOZZA, description="Stato elemento")
    attivo: bool = Field(True, description="Se attivo")

    # Metadata
    note: Optional[str] = Field(None, description="Note aggiuntive")


class ElementoEsempioCreate(ElementoEsempioBase):
    """Schema for creating a new elemento"""
    pass


class ElementoEsempioUpdate(BaseModel):
    """Schema for updating - all fields optional"""
    codice: Optional[str] = Field(None, min_length=1, max_length=20)
    titolo: Optional[str] = Field(None, min_length=1, max_length=200)
    descrizione: Optional[str] = None
    categoria_id: Optional[int] = None
    priorita_id: Optional[int] = None
    quantita: Optional[int] = Field(None, ge=0)
    importo: Optional[condecimal(max_digits=10, decimal_places=2)] = Field(None, ge=0)
    percentuale: Optional[condecimal(max_digits=5, decimal_places=2)] = Field(None, ge=0, le=100)
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    stato: Optional[StatoElemento] = None
    attivo: Optional[bool] = None
    note: Optional[str] = None


class ElementoEsempioResponse(ElementoEsempioBase):
    """Schema for API responses"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Nested domain data (for display)
    categoria_nome: Optional[str] = None
    categoria_colore: Optional[str] = None
    priorita_nome: Optional[str] = None
    priorita_colore: Optional[str] = None

    class Config:
        from_attributes = True


class ElementoEsempioListResponse(BaseModel):
    """Paginated list response"""
    items: list[ElementoEsempioResponse]
    total: int
    skip: int
    limit: int
