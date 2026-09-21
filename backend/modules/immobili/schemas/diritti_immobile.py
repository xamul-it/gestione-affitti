from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from ..models import TipoDiritto


class DirittoImmobileBase(BaseModel):
    unita_immobiliare_id: int
    proprietario_id: int
    tipo_diritto: TipoDiritto
    quota_percentuale: Optional[Decimal] = Field(None, ge=0, le=100)
    data_inizio: Optional[str] = None
    data_fine: Optional[str] = None
    note: Optional[str] = Field(None, max_length=500)


class DirittoImmobileCreate(DirittoImmobileBase):
    pass


class DirittoImmobileUpdate(BaseModel):
    tipo_diritto: Optional[TipoDiritto] = None
    quota_percentuale: Optional[Decimal] = Field(None, ge=0, le=100)
    data_inizio: Optional[str] = None
    data_fine: Optional[str] = None
    note: Optional[str] = Field(None, max_length=500)


class DirittoImmobileResponse(DirittoImmobileBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
