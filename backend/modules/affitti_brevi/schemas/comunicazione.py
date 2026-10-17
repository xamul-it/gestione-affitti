"""
Comunicazione Schemas
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ComunicazioneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    soggiorno_id: Optional[int] = None
    unita_immobiliare_id: Optional[int] = None
    tipo: str
    stato: str
    data_scadenza: datetime
    data_invio: Optional[datetime] = None
    scadenza_id: Optional[int] = None
    note: Optional[str] = None
    importo_tassa: Optional[Decimal] = None


class SegnaCompletataRequest(BaseModel):
    note: Optional[str] = None
