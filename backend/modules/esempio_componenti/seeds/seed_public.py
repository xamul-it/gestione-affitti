"""
Seed Public - Domain data per il modulo esempio_componenti.

Questo file contiene i dati di dominio che vengono popolati nello schema PUBLIC
durante la registrazione del modulo (endpoints.register).

I dati pubblici sono condivisi tra tutti i tenant.

Tabelle popolate:
- categorie_esempio: Categorie per classificare gli elementi
- priorita_esempio: Priorità per indicare l'urgenza
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# CATEGORIE ESEMPIO - Example categories for demonstration
# ============================================================================
CATEGORIE_ESEMPIO_DATA = [
    # (codice, nome, descrizione, colore, icona, ordine)
    ("CAT001", "Documentazione", "Elementi relativi a documentazione e procedure", "#3498db", "file-text", 1),
    ("CAT002", "Manutenzione", "Elementi relativi a manutenzione ordinaria e straordinaria", "#e74c3c", "wrench", 2),
    ("CAT003", "Amministrazione", "Elementi relativi a pratiche amministrative", "#9b59b6", "briefcase", 3),
    ("CAT004", "Comunicazioni", "Elementi relativi a comunicazioni e notifiche", "#2ecc71", "message-square", 4),
    ("CAT005", "Altro", "Elementi non classificati nelle altre categorie", "#95a5a6", "folder", 99),
]


# ============================================================================
# PRIORITÀ ESEMPIO - Example priorities for demonstration
# ============================================================================
PRIORITA_ESEMPIO_DATA = [
    # (codice, nome, livello, colore)
    ("P1", "Urgente", 4, "#e74c3c"),
    ("P2", "Alta", 3, "#f39c12"),
    ("P3", "Media", 2, "#3498db"),
    ("P4", "Bassa", 1, "#2ecc71"),
    ("P5", "Nessuna", 0, "#95a5a6"),
]


def seed_categorie_esempio(db: Session) -> int:
    """
    Seed categorie_esempio table in PUBLIC schema.

    Args:
        db: Database session (search_path should be set to public)

    Returns:
        Number of categories seeded (0 if already seeded)
    """
    # Ensure we're in public schema
    db.execute(text("SET search_path TO public"))

    # Check if already seeded
    result = db.execute(text("SELECT COUNT(*) FROM esem_categorie_esempio"))
    existing_count = result.scalar()

    if existing_count > 0:
        logger.info(f"[ESEMPIO] categorie_esempio already seeded ({existing_count} records)")
        return 0

    logger.info("[ESEMPIO] Seeding categorie_esempio...")
    seeded_count = 0

    for codice, nome, descrizione, colore, icona, ordine in CATEGORIE_ESEMPIO_DATA:
        try:
            db.execute(
                text("""
                    INSERT INTO esem_categorie_esempio
                    (codice, nome, descrizione, colore, icona, ordine, attivo)
                    VALUES (:codice, :nome, :descrizione, :colore, :icona, :ordine, true)
                """),
                {
                    "codice": codice,
                    "nome": nome,
                    "descrizione": descrizione,
                    "colore": colore,
                    "icona": icona,
                    "ordine": ordine
                }
            )
            seeded_count += 1
        except Exception as e:
            logger.error(f"[ESEMPIO] Error seeding categoria {codice}: {e}")

    db.commit()
    logger.info(f"[ESEMPIO] Successfully seeded {seeded_count} categorie_esempio")
    return seeded_count


def seed_priorita_esempio(db: Session) -> int:
    """
    Seed priorita_esempio table in PUBLIC schema.

    Args:
        db: Database session (search_path should be set to public)

    Returns:
        Number of priorities seeded (0 if already seeded)
    """
    # Ensure we're in public schema
    db.execute(text("SET search_path TO public"))

    # Check if already seeded
    result = db.execute(text("SELECT COUNT(*) FROM esem_priorita_esempio"))
    existing_count = result.scalar()

    if existing_count > 0:
        logger.info(f"[ESEMPIO] priorita_esempio already seeded ({existing_count} records)")
        return 0

    logger.info("[ESEMPIO] Seeding priorita_esempio...")
    seeded_count = 0

    for codice, nome, livello, colore in PRIORITA_ESEMPIO_DATA:
        try:
            db.execute(
                text("""
                    INSERT INTO esem_priorita_esempio
                    (codice, nome, livello, colore, attivo)
                    VALUES (:codice, :nome, :livello, :colore, true)
                """),
                {
                    "codice": codice,
                    "nome": nome,
                    "livello": livello,
                    "colore": colore
                }
            )
            seeded_count += 1
        except Exception as e:
            logger.error(f"[ESEMPIO] Error seeding priorita {codice}: {e}")

    db.commit()
    logger.info(f"[ESEMPIO] Successfully seeded {seeded_count} priorita_esempio")
    return seeded_count


def seed_all_public(db: Session) -> dict:
    """
    Seed all public domain data for the esempio_componenti module.

    This function is called by the core during module registration (endpoints.register).
    It populates all domain data tables in the PUBLIC schema.

    Args:
        db: Database session

    Returns:
        Dictionary with counts of seeded records per table
    """
    logger.info("[ESEMPIO] Starting public seed...")

    results = {
        "categorie_esempio": seed_categorie_esempio(db),
        "priorita_esempio": seed_priorita_esempio(db),
    }

    logger.info(f"[ESEMPIO] Public seed completed: {results}")
    return results
