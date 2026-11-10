"""
Core Scadenza owned by another record (a document, a role relation): opened,
moved and closed together with it. Flushes, never commits.
"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.platform.models import PrioritaScadenza, Scadenza, StatoScadenza
from app.core.platform.models.scadenza_log import ScadenzaLog

APERTE = (StatoScadenza.ATTIVA, StatoScadenza.SCADUTA)


def utente_sistema(db: Session) -> int:
    """System operations (migrations, sync): attributed to the first superuser."""
    return db.execute(text(
        "SELECT id FROM public.core_users ORDER BY is_superuser DESC, id LIMIT 1"
    )).scalar()


def apri_o_aggiorna(
    db: Session, *, scadenza_id: Optional[int], modulo: Optional[str], entity_type: str,
    entity_id: int, titolo: str, descrizione: str, data: date, user_id: int, nota_creazione: str,
) -> int:
    """Move the open scadenza to `data`, or create a new one. Returns its id."""
    scadenza = db.get(Scadenza, scadenza_id) if scadenza_id else None
    if scadenza is not None and scadenza.stato in APERTE:
        if scadenza.data_scadenza != data:
            scadenza.data_scadenza = data
            scadenza.modificato_il = datetime.utcnow()
        return scadenza.id
    scadenza = Scadenza(
        modulo=modulo, entity_type=entity_type, entity_id=entity_id, titolo=titolo[:200],
        descrizione=descrizione, data_scadenza=data, priorita=PrioritaScadenza.ALTA,
        stato=StatoScadenza.ATTIVA, creato_da=user_id,
    )
    db.add(scadenza)
    db.flush()
    db.add(ScadenzaLog.log_creation(scadenza_id=scadenza.id, user_id=user_id, note=nota_creazione))
    return scadenza.id


def chiudi(db: Session, scadenza_id: Optional[int], stato: StatoScadenza, note: str, user_id: int) -> None:
    """Close an open scadenza as COMPLETATA or ANNULLATA; no-op otherwise."""
    if not scadenza_id:
        return
    scadenza = db.get(Scadenza, scadenza_id)
    if scadenza is None or scadenza.stato not in APERTE:
        return
    scadenza.stato = stato
    scadenza.modificato_il = datetime.utcnow()
    if stato == StatoScadenza.COMPLETATA:
        scadenza.completato_da = user_id
        scadenza.completato_il = datetime.utcnow()
        db.add(ScadenzaLog.log_completion(scadenza_id=scadenza.id, user_id=user_id, note=note))
    else:
        db.add(ScadenzaLog.log_cancellation(scadenza_id=scadenza.id, user_id=user_id, note=note))
