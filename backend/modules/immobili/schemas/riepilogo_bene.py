"""'Who pays what' of a bene at a date (GET /beni/{id}/riepilogo): who, never how much."""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class SoggettoRuolo(BaseModel):
    soggetto_id: int
    nome: str
    ruolo: str
    quota: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class VoceRiepilogo(BaseModel):
    codice: str
    etichetta: str
    soggetti: List[SoggettoRuolo]
    norma: str

    model_config = ConfigDict(from_attributes=True)


class RiepilogoBeneResponse(BaseModel):
    data: date
    voci: List[VoceRiepilogo]
    avvisi: List[str]

    model_config = ConfigDict(from_attributes=True)
