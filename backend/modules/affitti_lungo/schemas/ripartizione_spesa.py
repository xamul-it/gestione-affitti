from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class RipartizioneSpesaBase(BaseModel):
    spesa_id: int
    unita_immobiliare_id: int
    importo_ripartito: float
    millesimi_applicati: Optional[float] = None
    consumo_applicato: Optional[float] = None
    occupanti_applicati: Optional[int] = None
    coefficiente_piano: Optional[float] = None
    importo_da_millesimi: Optional[float] = None
    importo_da_consumo: Optional[float] = None
    importo_da_occupanti: Optional[float] = None
    pagata: int = 0
    data_pagamento: Optional[datetime] = None
    note: Optional[str] = None


class RipartizioneSpesaCreate(RipartizioneSpesaBase):
    pass


class RipartizioneSpesaUpdate(BaseModel):
    spesa_id: Optional[int] = None
    unita_immobiliare_id: Optional[int] = None
    importo_ripartito: Optional[float] = None
    millesimi_applicati: Optional[float] = None
    consumo_applicato: Optional[float] = None
    occupanti_applicati: Optional[int] = None
    coefficiente_piano: Optional[float] = None
    importo_da_millesimi: Optional[float] = None
    importo_da_consumo: Optional[float] = None
    importo_da_occupanti: Optional[float] = None
    pagata: Optional[int] = None
    data_pagamento: Optional[datetime] = None
    note: Optional[str] = None


class RipartizioneSpesaResponse(RipartizioneSpesaBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
