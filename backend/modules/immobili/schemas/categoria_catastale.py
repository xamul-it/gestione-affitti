"""
Pydantic schemas for CategoriaCatastale.

Provides validation and serialization for Italian cadastral categories.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class CategoriaCatastaleBase(BaseModel):
    """Base schema with common fields."""
    codice: str = Field(..., max_length=10, description="Cadastral code (e.g., A/2, C/6)")
    nome: str = Field(..., max_length=200, description="Full descriptive name")
    gruppo: str = Field(..., max_length=1, description="Category group (A-F)")
    descrizione: Optional[str] = Field(None, description="Additional description")
    ordinamento: Optional[int] = Field(0, description="Sort order for UI")
    attiva: Optional[bool] = Field(True, description="Active flag")

    @field_validator("gruppo")
    @classmethod
    def validate_gruppo(cls, v: str) -> str:
        """Validate gruppo is one of A-F."""
        if v not in ["A", "B", "C", "D", "E", "F"]:
            raise ValueError("Gruppo must be one of: A, B, C, D, E, F")
        return v.upper()

    @field_validator("codice")
    @classmethod
    def validate_codice(cls, v: str) -> str:
        """Validate codice format."""
        if not v or len(v) < 2:
            raise ValueError("Codice must be at least 2 characters")
        return v.upper()


class CategoriaCatastaleCreate(CategoriaCatastaleBase):
    """Schema for creating a new categoria catastale."""
    pass


class CategoriaCatastaleUpdate(BaseModel):
    """Schema for updating an existing categoria catastale."""
    codice: Optional[str] = Field(None, max_length=10)
    nome: Optional[str] = Field(None, max_length=200)
    gruppo: Optional[str] = Field(None, max_length=1)
    descrizione: Optional[str] = None
    ordinamento: Optional[int] = None
    attiva: Optional[bool] = None


class CategoriaCatastale(CategoriaCatastaleBase):
    """Schema for categoria catastale response."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
