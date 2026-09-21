from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime

from .categoria_catastale import CategoriaCatastale


class UnitaImmobiliareBase(BaseModel):
    codice: Optional[str] = None  # Optional for import with auto-generation
    tipo: str
    condominio_id: Optional[int] = None
    indirizzo: str
    citta: str
    cap: Optional[str] = None
    provincia: Optional[str] = None
    superficie_mq: Optional[float] = None
    locali: Optional[int] = None
    piano: Optional[str] = None
    classe_energetica: Optional[str] = None
    rendita_catastale: Optional[float] = None
    foglio: Optional[str] = None
    particella: Optional[str] = None
    subalterno: Optional[str] = None
    descrizione: Optional[str] = None
    note: Optional[str] = None
    # New fields for automatismi
    categoria_catastale_id: Optional[int] = None
    codice_auto_generated: Optional[bool] = None
    indirizzo_parsed_warnings: Optional[List[str]] = None


class UnitaImmobiliareCreate(UnitaImmobiliareBase):
    """Schema for creating records with validation."""

    @field_validator('superficie_mq')
    @classmethod
    def validate_superficie_mq(cls, v):
        """Validate that superficie_mq is non-negative."""
        if v is not None and v < 0:
            raise ValueError('La superficie deve essere un valore non negativo')
        return v

    @field_validator('rendita_catastale')
    @classmethod
    def validate_rendita_catastale(cls, v):
        """Validate that rendita_catastale is non-negative."""
        if v is not None and v < 0:
            raise ValueError('La rendita catastale deve essere un valore non negativo')
        return v

    @field_validator('locali')
    @classmethod
    def validate_locali(cls, v):
        """Validate that locali is non-negative."""
        if v is not None and v < 0:
            raise ValueError('Il numero di locali deve essere un valore non negativo')
        return v


class UnitaImmobiliareUpdate(BaseModel):
    """Schema for updating records with validation."""
    codice: Optional[str] = None
    tipo: Optional[str] = None
    condominio_id: Optional[int] = None
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    cap: Optional[str] = None
    provincia: Optional[str] = None
    superficie_mq: Optional[float] = None
    locali: Optional[int] = None
    piano: Optional[str] = None
    classe_energetica: Optional[str] = None
    rendita_catastale: Optional[float] = None
    foglio: Optional[str] = None
    particella: Optional[str] = None
    subalterno: Optional[str] = None
    descrizione: Optional[str] = None
    note: Optional[str] = None
    # New fields for automatismi
    categoria_catastale_id: Optional[int] = None
    codice_auto_generated: Optional[bool] = None
    indirizzo_parsed_warnings: Optional[List[str]] = None

    @field_validator('superficie_mq')
    @classmethod
    def validate_superficie_mq(cls, v):
        """Validate that superficie_mq is non-negative."""
        if v is not None and v < 0:
            raise ValueError('La superficie deve essere un valore non negativo')
        return v

    @field_validator('rendita_catastale')
    @classmethod
    def validate_rendita_catastale(cls, v):
        """Validate that rendita_catastale is non-negative."""
        if v is not None and v < 0:
            raise ValueError('La rendita catastale deve essere un valore non negativo')
        return v

    @field_validator('locali')
    @classmethod
    def validate_locali(cls, v):
        """Validate that locali is non-negative."""
        if v is not None and v < 0:
            raise ValueError('Il numero di locali deve essere un valore non negativo')
        return v


class UnitaImmobiliareResponse(UnitaImmobiliareBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    # New fields included in response
    categoria_catastale_id: Optional[int] = None
    categoria_catastale: Optional[CategoriaCatastale] = None  # Nested relationship
    codice_auto_generated: Optional[bool] = None
    indirizzo_parsed_warnings: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


# Backward compatibility aliases
ImmobileBase = UnitaImmobiliareBase
ImmobileCreate = UnitaImmobiliareCreate
ImmobileUpdate = UnitaImmobiliareUpdate
ImmobileResponse = UnitaImmobiliareResponse
