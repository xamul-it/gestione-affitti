"""
Schemas for validating parsed document data on existing anagrafica entities.
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class CompleteDocumentoParsing(BaseModel):
    """
    Schema for completing a parsed document on an existing soggetto.
    """
    job_uuid: str = Field(..., description="DocumentJob UUID")
    apply_to_soggetto: bool = Field(True, description="Apply parsed data to soggetto fields")

    nome: Optional[str] = Field(None, max_length=100)
    cognome: Optional[str] = Field(None, max_length=100)
    codice_fiscale: Optional[str] = Field(None, max_length=16)
    data_nascita: Optional[str] = Field(None, description="Birth date YYYY-MM-DD")
    luogo_nascita: Optional[str] = Field(None, max_length=100)

    document_number: Optional[str] = Field(None, max_length=50)
    document_expiry: Optional[str] = Field(None, description="Document expiry YYYY-MM-DD")
    note: Optional[str] = Field(None, max_length=1000)

    @field_validator("data_nascita", "document_expiry")
    @classmethod
    def validate_date_format(cls, v):
        if v:
            from datetime import datetime
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError as exc:
                raise ValueError("Formato data non valido. Usa YYYY-MM-DD") from exc
        return v
