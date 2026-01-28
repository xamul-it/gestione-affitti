"""
Pydantic schemas for SoggettoAnagrafico (Italian Registry Subject).
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, datetime
from enum import Enum


class TipoSoggettoEnum(str, Enum):
    """Tipologia di soggetto anagrafico"""
    PERSONA_FISICA = "PERSONA_FISICA"
    PERSONA_GIURIDICA = "PERSONA_GIURIDICA"


class SoggettoAnagraficoBase(BaseModel):
    """Base schema for SoggettoAnagrafico"""
    tipo_soggetto: TipoSoggettoEnum

    # Link to User (optional - for system access)
    user_id: Optional[int] = None

    # Dati fiscali
    codice_fiscale: Optional[str] = Field(None, max_length=16)
    partita_iva: Optional[str] = Field(None, max_length=11)

    # Persona fisica
    nome: Optional[str] = Field(None, max_length=100)
    cognome: Optional[str] = Field(None, max_length=100)
    data_nascita: Optional[date] = None
    luogo_nascita: Optional[str] = Field(None, max_length=100)

    # Persona giuridica
    ragione_sociale: Optional[str] = Field(None, max_length=200)

    # Contatti
    email: Optional[str] = Field(None, max_length=255)
    telefono: Optional[str] = Field(None, max_length=20)
    cellulare: Optional[str] = Field(None, max_length=20)
    pec: Optional[str] = Field(None, max_length=255)

    # Indirizzo
    indirizzo: Optional[str] = Field(None, max_length=255)
    citta: Optional[str] = Field(None, max_length=100)
    cap: Optional[str] = Field(None, max_length=10)
    provincia: Optional[str] = Field(None, max_length=2)

    # Meta
    note: Optional[str] = Field(None, max_length=1000)
    attivo: bool = True


class SoggettoAnagraficoCreate(SoggettoAnagraficoBase):
    """Schema for creating a new SoggettoAnagrafico"""

    @field_validator('codice_fiscale', 'partita_iva')
    @classmethod
    def validate_fiscal_code(cls, v, info):
        """At least one fiscal identifier must be provided"""
        # This validation will be checked in the route
        return v


class SoggettoAnagraficoUpdate(BaseModel):
    """Schema for updating a SoggettoAnagrafico"""
    tipo_soggetto: Optional[TipoSoggettoEnum] = None

    # Link to User (optional - for system access)
    user_id: Optional[int] = None

    # Dati fiscali
    codice_fiscale: Optional[str] = Field(None, max_length=16)
    partita_iva: Optional[str] = Field(None, max_length=11)

    # Persona fisica
    nome: Optional[str] = Field(None, max_length=100)
    cognome: Optional[str] = Field(None, max_length=100)
    data_nascita: Optional[date] = None
    luogo_nascita: Optional[str] = Field(None, max_length=100)

    # Persona giuridica
    ragione_sociale: Optional[str] = Field(None, max_length=200)

    # Contatti
    email: Optional[str] = Field(None, max_length=255)
    telefono: Optional[str] = Field(None, max_length=20)
    cellulare: Optional[str] = Field(None, max_length=20)
    pec: Optional[str] = Field(None, max_length=255)

    # Indirizzo
    indirizzo: Optional[str] = Field(None, max_length=255)
    citta: Optional[str] = Field(None, max_length=100)
    cap: Optional[str] = Field(None, max_length=10)
    provincia: Optional[str] = Field(None, max_length=2)

    # Meta
    note: Optional[str] = Field(None, max_length=1000)
    attivo: Optional[bool] = None


class SoggettoAnagraficoResponse(SoggettoAnagraficoBase):
    """Schema for SoggettoAnagrafico response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompleteSoggettoFromDocument(BaseModel):
    """
    Schema for completing anagrafica creation from parsed document.

    Used in "create from document" workflow after MRZ parsing.
    """
    job_uuid: str = Field(..., description="DocumentJob UUID")

    # Required fields
    nome: str = Field(..., max_length=100, description="First name (from parsed data)")
    cognome: str = Field(..., max_length=100, description="Last name (from parsed data)")
    codice_fiscale: str = Field(..., max_length=16, description="Italian fiscal code (from parsed data)")

    # Optional fields (from parsed data or user input)
    data_nascita: Optional[str] = Field(None, description="Birth date YYYY-MM-DD (from parsed data)")
    luogo_nascita: Optional[str] = Field(None, max_length=100, description="Birth place (from parsed data)")

    # Contact info (user input)
    email: Optional[str] = Field(None, max_length=255)
    telefono: Optional[str] = Field(None, max_length=20)
    cellulare: Optional[str] = Field(None, max_length=20)

    # Address (user input)
    indirizzo: Optional[str] = Field(None, max_length=255)
    citta: Optional[str] = Field(None, max_length=100)
    cap: Optional[str] = Field(None, max_length=10)
    provincia: Optional[str] = Field(None, max_length=2)

    # Document info (from parsed data)
    document_number: Optional[str] = Field(None, max_length=50, description="Document number from ID")
    document_expiry: Optional[str] = Field(None, description="Document expiry YYYY-MM-DD")

    # Notes
    note: Optional[str] = Field(None, max_length=1000)

    @field_validator('data_nascita', 'document_expiry')
    @classmethod
    def validate_date_format(cls, v):
        """Validate date format YYYY-MM-DD"""
        if v:
            try:
                from datetime import datetime
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Formato data non valido. Usa YYYY-MM-DD")
        return v
