"""
Seed tenant data for Anagrafica Italiana module.

Supports optional test data seeding.
"""
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from .seed_soggetti_anagrafici import seed_soggetti_anagrafici

logger = logging.getLogger(__name__)

NOTA_ESEMPIO = "Dato di esempio"


def seed_tenant(
    db: Session,
    tenant_id: int | None = None,
    tenant_schema: str | None = None,
    seed_test_data: bool = False,
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

    # Only seed when explicitly requested with a boolean True.
    if seed_test_data is True:
        logger.info(
            "Seeding test data for anagrafica_italiana (tenant_id=%s, schema=%s)",
            tenant_id,
            tenant_schema,
        )
        # Generated people are random: create them once per tenant, marked
        # in the notes, so rerunning the example data adds nothing.
        if db.execute(text("SELECT 1 FROM anag_soggetti_anagrafici WHERE note = :n LIMIT 1"),
                      {"n": NOTA_ESEMPIO}).first():
            return results
        created = seed_soggetti_anagrafici(
            n_persone_fisiche=10,
            n_persone_giuridiche=5,
            db=db,
        )
        ids = [c["id"] for c in created or [] if c.get("id")]
        if ids and tenant_schema:
            # The generator commits: the next connection has lost the tenant path.
            db.execute(text(f'SET search_path TO "{tenant_schema}", public'))
        if ids:
            db.execute(text("UPDATE anag_soggetti_anagrafici SET note = :n WHERE id = ANY(:ids)"),
                       {"n": NOTA_ESEMPIO, "ids": ids})
            db.commit()
        results["test_data_seeded"] = len(created or [])

    return results
