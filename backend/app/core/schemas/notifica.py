"""Pydantic schemas for the generic Notifica (core notification service)."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class CanaleNotifica(str, Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    ENTRAMBI = "ENTRAMBI"


class StatoEmailNotifica(str, Enum):
    NON_RICHIESTA = "NON_RICHIESTA"
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class NotificaResponse(BaseModel):
    id: int
    tipo: str
    titolo: str
    corpo: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    link_url: Optional[str] = None
    canali: str
    stato_email: str
    letta: bool
    letta_il: Optional[datetime] = None
    creata_il: datetime

    class Config:
        from_attributes = True


class NotificaBadgeResponse(BaseModel):
    count_non_lette: int


class SegnaTutteLetteResponse(BaseModel):
    count: int
