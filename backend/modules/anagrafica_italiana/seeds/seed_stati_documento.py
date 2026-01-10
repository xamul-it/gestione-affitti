"""
Seed default document states for anagrafica module.
"""
from sqlalchemy.orm import Session
from anagrafica_italiana.models import StatoDocumento
import logging

logger = logging.getLogger(__name__)


def seed_stati_documento(db: Session):
    """Upsert default document states"""
    stati_documento = [
        {"codice": "VAL", "nome": "Valido", "descrizione": "Documento valido"},
        {"codice": "SCA", "nome": "In scadenza", "descrizione": "Documento in scadenza"},
        {"codice": "SCO", "nome": "Scaduto", "descrizione": "Documento scaduto"},
        {"codice": "SOS", "nome": "Sostituito", "descrizione": "Documento sostituito"},
        {"codice": "NAP", "nome": "Non applicabile", "descrizione": "Documento senza scadenza"},
    ]

    updated = 0
    created = 0

    for stato_data in stati_documento:
        existing = db.query(StatoDocumento).filter(
            StatoDocumento.codice == stato_data["codice"]
        ).first()
        if existing:
            existing.nome = stato_data["nome"]
            existing.descrizione = stato_data["descrizione"]
            existing.attivo = True
            updated += 1
        else:
            db.add(StatoDocumento(**stato_data))
            created += 1

    db.commit()
    logger.info("✅ Seed stati documento: %s created, %s updated", created, updated)
    return created + updated
