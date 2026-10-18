"""
Schema Pydantic per le risposte PEC (invio e audit).
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RispostaCreate(BaseModel):
    """Payload per inviare una risposta PEC."""

    destinatari: list[str]      # lista indirizzi email
    oggetto: str                # soggetto (il service aggiunge "Re: " se manca)
    corpo_testo: str            # testo plain obbligatorio
    corpo_html: str | None = None


class RispostaRead(BaseModel):
    """Response dopo invio risposta."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    messaggio_originale_id: int | None
    user_id: int
    destinatari: str | None
    oggetto_risposta: str | None
    smtp_status: str
    message_id_risposta: str | None
    hash_integrita: str | None
    inviato_at: datetime | None
    created_at: datetime
