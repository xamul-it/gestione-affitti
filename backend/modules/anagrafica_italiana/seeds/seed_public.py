"""
Seed public domain data for Anagrafica Italiana module.
"""
import logging
from sqlalchemy.orm import Session

from .seed_stati_documento import seed_stati_documento
from .seed_comuni_italia import seed_comuni_italia_minimal
from .seed_ruoli_azienda_tipi import seed_ruoli_azienda_tipi

logger = logging.getLogger(__name__)


def seed_public(db: Session) -> dict:
    """
    Seed public domain tables for the anagrafica_italiana module.

    Document types are not seeded here: they are declared in the manifest
    and synced by app.core.platform_services.document_type_sync.
    """
    results = {
        "stati_documento": seed_stati_documento(db),
        "comuni_italia": seed_comuni_italia_minimal(db),
        "ruoli_azienda_tipi": seed_ruoli_azienda_tipi(db),
    }
    logger.info("Anagrafica public seed results: %s", results)
    return results
