from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class MillesimiUnitaBase(BaseModel):
    unita_immobiliare_id: int
    tabella_millesimale_id: int
    millesimi: float
    piano: Optional[int] = None
    numero_occupanti: int = 0
    consumo: float = 0.0
    unita_misura_consumo: Optional[str] = None
    quota_fissa: Optional[float] = None


class MillesimiUnitaCreate(MillesimiUnitaBase):
    pass


class MillesimiUnitaUpdate(BaseModel):
    unita_immobiliare_id: Optional[int] = None
    tabella_millesimale_id: Optional[int] = None
    millesimi: Optional[float] = None
    piano: Optional[int] = None
    numero_occupanti: Optional[int] = None
    consumo: Optional[float] = None
    unita_misura_consumo: Optional[str] = None
    quota_fissa: Optional[float] = None


class MillesimiUnitaResponse(MillesimiUnitaBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
