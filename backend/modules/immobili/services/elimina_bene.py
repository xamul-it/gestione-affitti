"""
Delete a bene (unit or land parcel) for good.

Rights, tenant assignments, cadastral changes, recurring costs and land
portions go with ON DELETE CASCADE. Documents, scadenze and core relations
point to the bene by entity_type IMMOBILE + entity_id, without a FK: they
are removed here (document scadenze and relation scadenze are cancelled).
The document files stay in storage, as in the phase 1 reset: nothing is
lost by mistake.
"""
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.platform.models import Documento, Scadenza
from app.core.platform.models.scadenza import StatoScadenza
from app.core.platform_services.documento_service import DocumentoService
from app.core.platform_services.relazione_service import RelazioneService
from app.core.platform_services.scadenze_collegate import APERTE, chiudi, utente_sistema

from ..models import Bene

ENTITY_TYPE = "IMMOBILE"


def elimina_bene(db: Session, bene: Bene, user_id: Optional[int]) -> None:
    """Remove the bene and what points to it; the caller commits."""
    bene_id = bene.id
    RelazioneService(db, None, user_id).elimina_per_oggetto(ENTITY_TYPE, bene_id)

    documenti = DocumentoService(db, None, user_id)
    for (documento_id,) in db.query(Documento.id).filter(
        Documento.entity_type == ENTITY_TYPE, Documento.entity_id == bene_id
    ).all():
        documenti.elimina(documento_id)

    utente = user_id or utente_sistema(db)
    for (scadenza_id,) in db.query(Scadenza.id).filter(
        func.upper(Scadenza.entity_type) == ENTITY_TYPE,
        Scadenza.entity_id == bene_id,
        Scadenza.stato.in_(APERTE),
    ).all():
        chiudi(db, scadenza_id, StatoScadenza.CANCELLATA, f"Bene {bene_id} eliminato", utente)

    db.delete(bene)
    db.flush()
