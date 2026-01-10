"""
TassaSoggiorno Schemas - Pydantic models for tourist tax configuration and tiers
"""
from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from ..models.tassa_soggiorno_config import TipoCalcoloTassa


# ==================== TassaSoggiornoConfig Schemas ====================

class TassaSoggiornoConfigBase(BaseModel):
    """Base schema for tourist tax configuration"""
    comune_id: int = Field(..., description="ID del comune")
    comune_nome: str = Field(..., max_length=200, description="Nome comune per visualizzazione")
    tipo_calcolo: TipoCalcoloTassa = Field(..., description="Tipo di calcolo tassa")

    # Calculation parameters
    importo_fisso: Optional[Decimal] = Field(None, ge=0, description="Importo fisso per notte per persona (FISSO)")
    percentuale: Optional[Decimal] = Field(None, ge=0, le=100, description="Percentuale del prezzo notte (PERCENTUALE)")

    # Exemptions
    eta_minima: Optional[int] = Field(0, ge=0, le=120, description="Età minima soggetta a tassa")
    eta_massima: Optional[int] = Field(None, ge=0, le=120, description="Età massima soggetta a tassa")
    notti_max: Optional[int] = Field(None, ge=1, le=365, description="Numero max notti tassabili")

    # Validity period
    data_inizio_validita: date = Field(..., description="Data inizio validità configurazione")
    data_fine_validita: Optional[date] = Field(None, description="Data fine validità (NULL = attiva)")

    # Status and notes
    attiva: bool = Field(True, description="Configurazione attiva")
    note: Optional[str] = Field(None, description="Note su regolamento comunale")


class TassaSoggiornoConfigCreate(TassaSoggiornoConfigBase):
    """Schema for creating a new tourist tax configuration"""
    pass


class TassaSoggiornoConfigUpdate(BaseModel):
    """Schema for updating an existing tourist tax configuration"""
    comune_id: Optional[int] = None
    comune_nome: Optional[str] = Field(None, max_length=200)
    tipo_calcolo: Optional[TipoCalcoloTassa] = None

    # Calculation parameters
    importo_fisso: Optional[Decimal] = Field(None, ge=0)
    percentuale: Optional[Decimal] = Field(None, ge=0, le=100)

    # Exemptions
    eta_minima: Optional[int] = Field(None, ge=0, le=120)
    eta_massima: Optional[int] = Field(None, ge=0, le=120)
    notti_max: Optional[int] = Field(None, ge=1, le=365)

    # Validity period
    data_inizio_validita: Optional[date] = None
    data_fine_validita: Optional[date] = None

    # Status and notes
    attiva: Optional[bool] = None
    note: Optional[str] = None


class TassaSoggiornoConfigResponse(TassaSoggiornoConfigBase):
    """Schema for API responses"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Related data
    scaglioni: List["TassaSoggiornoScaglioneResponse"] = []

    model_config = ConfigDict(from_attributes=True)


# ==================== TassaSoggiornoScaglione Schemas ====================

class TassaSoggiornoScaglioneBase(BaseModel):
    """Base schema for tourist tax tier"""
    notte_da: int = Field(..., ge=1, description="Prima notte di questo scaglione")
    notte_a: Optional[int] = Field(None, ge=1, description="Ultima notte (NULL = infinito)")
    importo: Decimal = Field(..., ge=0, description="Importo per notte per persona in questo scaglione")


class TassaSoggiornoScaglioneCreate(TassaSoggiornoScaglioneBase):
    """Schema for creating a new tier"""
    config_id: int = Field(..., description="ID della configurazione")


class TassaSoggiornoScaglioneUpdate(BaseModel):
    """Schema for updating an existing tier"""
    notte_da: Optional[int] = Field(None, ge=1)
    notte_a: Optional[int] = Field(None, ge=1)
    importo: Optional[Decimal] = Field(None, ge=0)


class TassaSoggiornoScaglioneResponse(TassaSoggiornoScaglioneBase):
    """Schema for API responses"""
    id: int
    config_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== Config with Scaglioni (for creation) ====================

class TassaSoggiornoConfigWithScaglioni(TassaSoggiornoConfigCreate):
    """Schema for creating config with tiers in one request"""
    scaglioni: List[TassaSoggiornoScaglioneBase] = Field(
        default_factory=list,
        description="Scaglioni da creare (solo per tipo_calcolo=SCAGLIONI)"
    )


# Rebuild models to resolve forward references (Pydantic v2 requirement)
TassaSoggiornoConfigResponse.model_rebuild()
