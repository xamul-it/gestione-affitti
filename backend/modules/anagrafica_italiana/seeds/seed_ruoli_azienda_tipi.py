"""
Seed default business role types for anagrafica module.
"""
import logging
from sqlalchemy.orm import Session

from anagrafica_italiana.models import RuoloAziendaTipo

logger = logging.getLogger(__name__)


def seed_ruoli_azienda_tipi(db: Session) -> int:
    """Upsert default business role types."""
    ruoli = [
        {"nome": "Amministratore", "descrizione": "Amministratore dell'azienda"},
        {"nome": "Direttore", "descrizione": "Direzione generale"},
        {"nome": "Responsabile", "descrizione": "Responsabile di funzione"},
        {"nome": "Legale Rappresentante", "descrizione": "Rappresentante legale"},
        {"nome": "Titolare", "descrizione": "Titolare dell'azienda"},
        {"nome": "Socio", "descrizione": "Socio dell'azienda"},
        {"nome": "Contabile", "descrizione": "Contabilita e amministrazione"},
        {"nome": "Segreteria", "descrizione": "Supporto segreteria"},
        {"nome": "Tecnico", "descrizione": "Ruolo tecnico operativo"},
        {"nome": "Altro", "descrizione": "Altro ruolo"},
    ]

    created = 0
    updated = 0

    for ruolo_data in ruoli:
        existing = (
            db.query(RuoloAziendaTipo)
            .filter(RuoloAziendaTipo.nome == ruolo_data["nome"])
            .first()
        )
        if existing:
            existing.descrizione = ruolo_data["descrizione"]
            existing.attivo = True
            updated += 1
        else:
            db.add(RuoloAziendaTipo(**ruolo_data))
            created += 1

    db.commit()
    logger.info("✅ Seeded ruoli_azienda_tipi: %s created, %s updated", created, updated)
    return created + updated
