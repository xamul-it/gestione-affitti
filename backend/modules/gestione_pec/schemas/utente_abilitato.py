"""
Schema Pydantic per PecUtenteAbilitato.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UtenteAbilitatoCreate(BaseModel):
    """Payload per abilitare un utente a una casella PEC."""

    user_id: int
    puo_rispondere: bool = False
    notifica_email: bool = True


class UtenteAbilitatoUpdate(BaseModel):
    """Payload per aggiornare i permessi di un utente abilitato — tutti opzionali."""

    puo_rispondere: bool | None = None
    notifica_email: bool | None = None


class UtenteAbilitatoRead(BaseModel):
    """Response schema per un utente abilitato a una casella PEC."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    casella_id: int
    user_id: int
    puo_rispondere: bool
    notifica_email: bool
    created_at: datetime
