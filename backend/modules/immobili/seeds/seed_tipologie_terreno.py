"""
Seed Tipologie Terreno - Land type classifications.

Seeds the tipologie_terreno table with standard land types
as defined in the functional analysis document.
"""
from sqlalchemy.orm import Session
from ..models import TipologiaTerreno
import logging

logger = logging.getLogger(__name__)


# Standard land type classifications (from functional analysis)
TIPOLOGIE_SEED_DATA = [
    # (codice, nome, descrizione, ordinamento)
    ("AGR", "Agricolo",
     "Terreno agricolo o coltivabile destinato all'attività agricola", 1),
    ("EDI", "Edificabile",
     "Terreno edificabile destinato a costruzioni residenziali, commerciali o industriali", 2),
    ("BOS", "Bosco/Forestale",
     "Terreno boschivo o forestale con copertura arborea", 3),
    ("IND", "Industriale",
     "Terreno destinato ad uso industriale o artigianale", 4),
    ("ALT", "Altro",
     "Qualsiasi altra tipologia di terreno non classificata nelle categorie precedenti", 99),
]


def seed_tipologie_terreno(db: Session) -> int:
    """
    Seed tipologie_terreno table with standard land types.

    This seeds the PUBLIC schema table with platform-level domain data.
    Tenant-specific types can be added later with tenant_id set.

    Args:
        db: Database session (should be connected to public schema)

    Returns:
        Number of tipologie seeded (0 if already seeded)
    """
    # Check if already seeded (only check platform types where tenant_id is NULL)
    existing_count = db.query(TipologiaTerreno).filter(
        TipologiaTerreno.tenant_id.is_(None)
    ).count()

    if existing_count > 0:
        logger.info(f"Tipologie terreno already seeded ({existing_count} platform records)")
        return 0

    logger.info("Seeding tipologie terreno...")
    seeded_count = 0

    for codice, nome, descrizione, ordinamento in TIPOLOGIE_SEED_DATA:
        try:
            tipologia = TipologiaTerreno(
                codice=codice,
                nome=nome,
                descrizione=descrizione,
                ordinamento=ordinamento,
                attiva=True,
                tenant_id=None  # Platform-level, shared by all tenants
            )
            db.add(tipologia)
            seeded_count += 1
        except Exception as e:
            logger.error(f"Error seeding tipologia {codice}: {e}")

    db.commit()
    logger.info(f"Successfully seeded {seeded_count} tipologie terreno")
    return seeded_count
