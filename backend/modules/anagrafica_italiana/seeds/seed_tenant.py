"""
Seed tenant data for Anagrafica Italiana module.

Supports optional test data seeding.
"""
import logging
from sqlalchemy.orm import Session

from .seed_soggetti_anagrafici import seed_soggetti_anagrafici

logger = logging.getLogger(__name__)


def seed_tenant(
    db: Session,
    seed_test_data: bool = False,
    tenant_id: int | None = None,
    tenant_schema: str | None = None,
) -> dict:
    """
    Seed tenant-level data for anagrafica_italiana.

    Args:
        db: SQLAlchemy session
        seed_test_data: If True, generate sample anagrafiche
        tenant_id: Optional tenant ID
        tenant_schema: Optional tenant schema name
    """
    results = {"test_data_seeded": 0}

    if seed_test_data:
        logger.info(
            "Seeding test data for anagrafica_italiana (tenant_id=%s, schema=%s)",
            tenant_id,
            tenant_schema,
        )
        created = seed_soggetti_anagrafici(
            n_persone_fisiche=10,
            n_persone_giuridiche=5,
            db=db,
        )
        results["test_data_seeded"] = len(created or [])

    return results
