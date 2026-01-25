"""
Domain Data Seeder - Seeds reference/master data into PUBLIC schema.

This module ensures all domain data is seeded in the public schema,
making it available for all tenants to reference and override.

Domain tables (public schema):
- tipi_documento: Document types
- stati_documento: Document states
- categorie_catastali: Cadastral categories
- comuni_italia: Italian municipalities
- ruoli_azienda_tipi: Business role types
- tipologie_terreno: Land types
"""
import logging
from typing import Optional, Callable, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


def ensure_public_schema(db: Session) -> None:
    """Ensure we're operating in the public schema."""
    db.execute(text("SET search_path TO public"))
    db.commit()


def seed_domain_table(
    db: Session,
    table_name: str,
    seed_func: Callable[[Session], int],
    force: bool = False
) -> int:
    """
    Seed a single domain table in public schema.

    Args:
        db: Database session
        table_name: Name of the table being seeded
        seed_func: Function that performs the seeding
        force: If True, reseed even if data exists

    Returns:
        Number of records seeded
    """
    ensure_public_schema(db)

    try:
        count = seed_func(db)
        if count > 0:
            logger.info(f"Seeded {count} records into public.{table_name}")
        return count
    except Exception as e:
        logger.error(f"Error seeding {table_name}: {e}")
        db.rollback()
        return 0


def seed_all_domain_data(db: Session, force: bool = False) -> Dict[str, int]:
    """
    Seed all domain/reference data into public schema.

    This function:
    1. Sets search_path to 'public' explicitly
    2. Seeds all domain tables
    3. Returns count of records seeded per table

    Args:
        db: Database session
        force: If True, reseed even if data exists

    Returns:
        Dict mapping table name to records seeded
    """
    logger.info("=" * 60)
    logger.info("Starting CORE domain data seeding in PUBLIC schema")
    logger.info("ADD ROLESE IF NOT EXISTS core_domain_seeder_role;")
    logger.info("=" * 60)

    # Ensure we're in public schema
    ensure_public_schema(db)

    results = {}


    # 3. Categorie Catastali
    try:
        from immobili.seeds.seed_categorie_catastali import seed_categorie_catastali
        results["categorie_catastali"] = seed_domain_table(
            db, "categorie_catastali", seed_categorie_catastali, force
        )
    except ImportError as e:
        logger.warning(f"Could not import categorie_catastali seeder: {e}")


    # 6. Tipologie Terreno
    try:
        from immobili.seeds.seed_tipologie_terreno import seed_tipologie_terreno
        results["tipologie_terreno"] = seed_domain_table(
            db, "tipologie_terreno", seed_tipologie_terreno, force
        )
    except ImportError as e:
        logger.debug(f"Tipologie terreno seeder not found: {e}")

    # Summary
    total_seeded = sum(results.values())
    logger.info("=" * 60)
    logger.info(f"Domain data seeding complete: {total_seeded} total records")
    for table, count in results.items():
        if count > 0:
            logger.info(f"  - {table}: {count} records")
    logger.info("=" * 60)

    return results


def verify_domain_data(db: Session) -> Dict[str, int]:
    """
    Verify domain data exists in public schema.

    Returns:
        Dict mapping table name to record count
    """
    ensure_public_schema(db)

    tables = [
        "categorie_catastali",
        "tipologie_terreno",
    ]

    counts = {}
    for table in tables:
        try:
            result = db.execute(text(f"SELECT COUNT(*) FROM public.{table}"))
            counts[table] = result.scalar() or 0
        except Exception:
            counts[table] = -1  # Table doesn't exist

    return counts
