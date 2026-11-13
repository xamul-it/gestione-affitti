"""
Pydantic schemas for Terreno (land parcel), a bene of the Catasto Terreni
with one or more portions. Surface is always in m² and computed by the
server as the sum of the portions.
"""
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .tipologia_terreno import TipologiaTerrenoSimple


class TerrenoPorzioneIn(BaseModel):
    """One portion of the parcel (visura: porzione, qualità, classe, superficie, redditi)."""
    porzione: Optional[str] = Field(None, max_length=5, description="Portion code, e.g. AA")
    qualita: str = Field(..., min_length=1, max_length=100, description="Quality, e.g. SEMINATIVO, ENTE URBANO")
    classe: Optional[str] = Field(None, max_length=10)
    superficie_mq: float = Field(..., ge=0, description="Surface in m²")
    reddito_dominicale: Optional[Decimal] = Field(None, ge=0)
    reddito_agrario: Optional[Decimal] = Field(None, ge=0)
    deduzioni: Optional[str] = Field(None, max_length=100)

    @field_validator("porzione", "classe")
    @classmethod
    def maiuscolo(cls, v: Optional[str]) -> Optional[str]:
        v = v.strip().upper() if v else v
        return v or None

    @field_validator("qualita")
    @classmethod
    def qualita_non_vuota(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("La qualità della porzione è obbligatoria")
        return v


class TerrenoPorzioneOut(TerrenoPorzioneIn):
    id: int

    model_config = ConfigDict(from_attributes=True)


def _provincia(v: Optional[str]) -> Optional[str]:
    if v:
        if len(v) != 2:
            raise ValueError("Provincia must be exactly 2 characters")
        return v.upper()
    return v


class TerrenoCreate(BaseModel):
    """New land parcel with its common bene fields and at least one portion."""
    codice: str = Field(..., min_length=1, max_length=50, description="Unique code among all beni")
    nome: Optional[str] = Field(None, max_length=255)
    descrizione: Optional[str] = None
    tipologia_id: Optional[int] = None
    indirizzo: Optional[str] = Field(None, max_length=255, description="Address or locality")
    comune: str = Field(..., max_length=100)
    cap: Optional[str] = Field(None, max_length=10)
    provincia: str = Field(..., max_length=2)
    nazione: Optional[str] = Field("Italia", max_length=100)
    sezione_catastale: Optional[str] = Field(None, max_length=20)
    foglio: Optional[str] = Field(None, max_length=20)
    particella: Optional[str] = Field(None, max_length=20)
    subalterno: Optional[str] = Field(None, max_length=20)
    note: Optional[str] = None
    attivo: Optional[bool] = True
    edificabile: Optional[bool] = False
    esente_imu_montano: Optional[bool] = False
    servitu: Optional[str] = None
    porzioni: List[TerrenoPorzioneIn] = Field(..., min_length=1)

    @field_validator("codice")
    @classmethod
    def validate_codice(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("provincia")
    @classmethod
    def validate_provincia(cls, v: str) -> str:
        return _provincia(v)


class TerrenoUpdate(BaseModel):
    """All optional; `porzioni`, when present, replaces the existing portions."""
    codice: Optional[str] = Field(None, min_length=1, max_length=50)
    nome: Optional[str] = Field(None, max_length=255)
    descrizione: Optional[str] = None
    tipologia_id: Optional[int] = None
    indirizzo: Optional[str] = Field(None, max_length=255)
    comune: Optional[str] = Field(None, max_length=100)
    cap: Optional[str] = Field(None, max_length=10)
    provincia: Optional[str] = Field(None, max_length=2)
    nazione: Optional[str] = Field(None, max_length=100)
    sezione_catastale: Optional[str] = Field(None, max_length=20)
    foglio: Optional[str] = Field(None, max_length=20)
    particella: Optional[str] = Field(None, max_length=20)
    subalterno: Optional[str] = Field(None, max_length=20)
    note: Optional[str] = None
    attivo: Optional[bool] = None
    edificabile: Optional[bool] = None
    esente_imu_montano: Optional[bool] = None
    servitu: Optional[str] = None
    porzioni: Optional[List[TerrenoPorzioneIn]] = Field(None, min_length=1)

    @field_validator("codice")
    @classmethod
    def validate_codice(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().upper() if v else v

    @field_validator("provincia")
    @classmethod
    def validate_provincia(cls, v: Optional[str]) -> Optional[str]:
        return _provincia(v)


class TerrenoResponse(BaseModel):
    id: int
    tipo_bene: str
    codice: str
    nome: Optional[str] = None
    descrizione: Optional[str] = None
    tipologia_id: Optional[int] = None
    tipologia: Optional[TipologiaTerrenoSimple] = None
    indirizzo: Optional[str] = None
    comune: Optional[str] = None
    cap: Optional[str] = None
    provincia: Optional[str] = None
    nazione: Optional[str] = None
    sezione_catastale: Optional[str] = None
    foglio: Optional[str] = None
    particella: Optional[str] = None
    subalterno: Optional[str] = None
    note: Optional[str] = None
    attivo: bool
    edificabile: bool
    esente_imu_montano: bool
    servitu: Optional[str] = None
    superficie_mq: Optional[float] = None
    reddito_dominicale_totale: Optional[Decimal] = None
    reddito_agrario_totale: Optional[Decimal] = None
    porzioni: List[TerrenoPorzioneOut] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Kept for imports that still use the old name.
TerrenoBase = TerrenoCreate
