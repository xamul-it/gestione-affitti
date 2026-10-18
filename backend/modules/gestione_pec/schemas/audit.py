"""
Schema Pydantic per PecAuditAccesso e PecAuditRisposta.
"""
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict


class AuditAccessoRead(BaseModel):
    """Response schema per un record di audit accesso."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    casella_id: int | None
    messaggio_id: int | None
    user_id: int
    azione: str
    ip_address: str | None
    user_agent: str | None
    dettagli: dict[str, Any] | None
    timestamp: datetime


class AuditRispostaRead(BaseModel):
    """Response schema per un record di audit risposta."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    casella_id: int | None
    messaggio_originale_id: int | None
    user_id: int
    destinatari: str | None
    oggetto_risposta: str | None
    corpo_risposta_testo: str | None
    corpo_risposta_html: str | None
    message_id_risposta: str | None
    snapshot_da: str | None
    snapshot_oggetto: str | None
    snapshot_corpo_testo: str | None
    snapshot_data_invio: datetime | None
    smtp_status: str | None
    smtp_error: str | None
    hash_integrita: str | None
    inviato_at: datetime | None
    created_at: datetime
