from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime


class IncassoBase(BaseModel):
    contratto_id: int
    data_incasso: date
    importo: float
    mese_riferimento: str
    metodo_pagamento: Optional[str] = None
    numero_ricevuta: Optional[str] = None
    note: Optional[str] = None


class IncassoCreate(IncassoBase):
    pass


class IncassoUpdate(BaseModel):
    contratto_id: Optional[int] = None
    data_incasso: Optional[date] = None
    importo: Optional[float] = None
    mese_riferimento: Optional[str] = None
    metodo_pagamento: Optional[str] = None
    numero_ricevuta: Optional[str] = None
    note: Optional[str] = None


class IncassoResponse(IncassoBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
