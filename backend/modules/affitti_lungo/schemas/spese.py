from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime
from ..models import CategoriaSpesa


class SpesaBase(BaseModel):
    unita_immobiliare_id: int
    tabella_millesimale_id: Optional[int] = None
    data: date
    importo: float
    categoria: CategoriaSpesa
    descrizione: str
    fornitore: Optional[str] = None
    numero_fattura: Optional[str] = None
    pagata: int = 0
    data_pagamento: Optional[date] = None
    metodo_pagamento: Optional[str] = None
    spesa_condominiale: int = 0
    ripartita: int = 0
    note: Optional[str] = None


class SpesaCreate(SpesaBase):
    pass


class SpesaUpdate(BaseModel):
    unita_immobiliare_id: Optional[int] = None
    tabella_millesimale_id: Optional[int] = None
    data: Optional[date] = None
    importo: Optional[float] = None
    categoria: Optional[CategoriaSpesa] = None
    descrizione: Optional[str] = None
    fornitore: Optional[str] = None
    numero_fattura: Optional[str] = None
    pagata: Optional[int] = None
    data_pagamento: Optional[date] = None
    metodo_pagamento: Optional[str] = None
    spesa_condominiale: Optional[int] = None
    ripartita: Optional[int] = None
    note: Optional[str] = None


class SpesaResponse(SpesaBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
