from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from ..models import TipoRipartizione


class TabellaMillesimaleBase(BaseModel):
    condominio_id: int
    nome: str
    codice: str
    tipo_ripartizione: TipoRipartizione = TipoRipartizione.MILLESIMI
    percentuale_millesimi: float = 100.0
    percentuale_consumo: float = 0.0
    percentuale_occupanti: float = 0.0
    descrizione: Optional[str] = None
    note: Optional[str] = None
    attiva: bool = True

    @field_validator('percentuale_millesimi', 'percentuale_consumo', 'percentuale_occupanti')
    @classmethod
    def validate_percentuali(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Le percentuali devono essere tra 0 e 100')
        return v


class TabellaMillesimaleCreate(TabellaMillesimaleBase):
    pass


class TabellaMillesimaleUpdate(BaseModel):
    condominio_id: Optional[int] = None
    nome: Optional[str] = None
    codice: Optional[str] = None
    tipo_ripartizione: Optional[TipoRipartizione] = None
    percentuale_millesimi: Optional[float] = None
    percentuale_consumo: Optional[float] = None
    percentuale_occupanti: Optional[float] = None
    descrizione: Optional[str] = None
    note: Optional[str] = None
    attiva: Optional[bool] = None


class TabellaMillesimaleResponse(TabellaMillesimaleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
