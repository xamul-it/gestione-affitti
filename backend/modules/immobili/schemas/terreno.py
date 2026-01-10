"""
Pydantic schemas for Terreno (Land).

Provides validation and serialization for land parcels.
"""
from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

from .tipologia_terreno import TipologiaTerrenoSimple


class TerrenoBase(BaseModel):
    """Base schema with common fields for land parcels."""

    # Identification
    codice: str = Field(..., max_length=50, description="Unique code (e.g., TER-001)")
    nome: str = Field(..., max_length=255, description="Descriptive name")
    descrizione: Optional[str] = Field(None, description="Extended description")

    # Classification - FK to tipologie_terreno
    tipologia_id: Optional[int] = Field(None, description="Land type ID (FK to tipologie_terreno)")

    # Location
    indirizzo: Optional[str] = Field(None, max_length=255, description="Address or locality")
    comune: str = Field(..., max_length=100, description="Municipality")
    cap: Optional[str] = Field(None, max_length=10, description="Postal code")
    provincia: str = Field(..., max_length=2, description="Province code (2 letters)")
    nazione: Optional[str] = Field("Italia", max_length=100, description="Country")

    # Physical characteristics
    superficie: float = Field(..., gt=0, description="Surface area")
    unita_misura_superficie: Optional[str] = Field("mq", description="Unit of measure (mq or ha)")

    # Cadastral data
    sezione_catastale: Optional[str] = Field(None, max_length=20, description="Cadastral section")
    foglio: Optional[str] = Field(None, max_length=20, description="Sheet number")
    particella: Optional[str] = Field(None, max_length=20, description="Parcel number")
    subalterno: Optional[str] = Field(None, max_length=20, description="Sub-unit (rare for land)")
    qualita_coltura: Optional[str] = Field(None, max_length=100, description="Crop quality type")
    classe_catastale: Optional[str] = Field(None, max_length=10, description="Cadastral class")

    # Fiscal values
    reddito_dominicale: Optional[Decimal] = Field(None, ge=0, description="Dominical income")
    reddito_agrario: Optional[Decimal] = Field(None, ge=0, description="Agricultural income")

    # Notes
    note: Optional[str] = Field(None, description="Additional notes")

    # Status
    attivo: Optional[bool] = Field(True, description="Active flag")

    @field_validator("codice")
    @classmethod
    def validate_codice(cls, v: str) -> str:
        """Ensure codice is uppercase."""
        if v:
            return v.upper()
        return v

    @field_validator("provincia")
    @classmethod
    def validate_provincia(cls, v: str) -> str:
        """Validate provincia is 2 uppercase letters."""
        if v:
            if len(v) != 2:
                raise ValueError("Provincia must be exactly 2 characters")
            return v.upper()
        return v

    @field_validator("unita_misura_superficie")
    @classmethod
    def validate_unita_misura(cls, v: Optional[str]) -> Optional[str]:
        """Validate unit of measure."""
        if v and v.lower() not in ["mq", "ha"]:
            raise ValueError("Unità di misura must be 'mq' or 'ha'")
        return v.lower() if v else "mq"


class TerrenoCreate(TerrenoBase):
    """Schema for creating a new terreno."""
    pass


class TerrenoUpdate(BaseModel):
    """Schema for updating an existing terreno. All fields are optional."""

    # Identification
    codice: Optional[str] = Field(None, max_length=50)
    nome: Optional[str] = Field(None, max_length=255)
    descrizione: Optional[str] = None

    # Classification - FK
    tipologia_id: Optional[int] = None

    # Location
    indirizzo: Optional[str] = Field(None, max_length=255)
    comune: Optional[str] = Field(None, max_length=100)
    cap: Optional[str] = Field(None, max_length=10)
    provincia: Optional[str] = Field(None, max_length=2)
    nazione: Optional[str] = Field(None, max_length=100)

    # Physical characteristics
    superficie: Optional[float] = Field(None, gt=0)
    unita_misura_superficie: Optional[str] = None

    # Cadastral data
    sezione_catastale: Optional[str] = Field(None, max_length=20)
    foglio: Optional[str] = Field(None, max_length=20)
    particella: Optional[str] = Field(None, max_length=20)
    subalterno: Optional[str] = Field(None, max_length=20)
    qualita_coltura: Optional[str] = Field(None, max_length=100)
    classe_catastale: Optional[str] = Field(None, max_length=10)

    # Fiscal values
    reddito_dominicale: Optional[Decimal] = Field(None, ge=0)
    reddito_agrario: Optional[Decimal] = Field(None, ge=0)

    # Notes
    note: Optional[str] = None

    # Status
    attivo: Optional[bool] = None

    @field_validator("provincia")
    @classmethod
    def validate_provincia(cls, v: Optional[str]) -> Optional[str]:
        """Validate provincia is 2 uppercase letters."""
        if v:
            if len(v) != 2:
                raise ValueError("Provincia must be exactly 2 characters")
            return v.upper()
        return v


class TerrenoResponse(TerrenoBase):
    """Schema for terreno response with metadata."""
    id: int
    tipologia: Optional[TipologiaTerrenoSimple] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
