"""
Schema Pydantic per PecMessaggio.
"""
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict


class MessaggioRead(BaseModel):
    """Response schema per un messaggio PEC."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    casella_id: int
    uid_imap: str
    message_id: str | None
    in_reply_to: str | None
    thread_id: str | None
    da: str
    a: str | None
    cc: str | None
    oggetto: str | None
    data_invio: datetime | None
    data_ricezione: datetime
    corpo_testo: str | None
    corpo_html: str | None
    allegati_meta: list[dict[str, Any]] | None
    is_letto: bool
    is_risposto: bool
    hash_contenuto: str | None
    created_at: datetime


class MessaggioList(BaseModel):
    """Response schema compatto per elenco messaggi."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    casella_id: int
    uid_imap: str
    da: str
    oggetto: str | None
    data_invio: datetime | None
    data_ricezione: datetime
    is_letto: bool
    is_risposto: bool
    allegati_meta: list[dict[str, Any]] | None
