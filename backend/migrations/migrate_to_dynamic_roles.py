"""
Migrazione al sistema di ruoli dinamici.

Popola la tabella soggetti_ruoli con i dati esistenti dalle tabelle
proprietari, affittuari e tecnici.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.services.role_registry import RoleRegistry
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(str(settings.DATABASE_URL))
SessionLocal = sessionmaker(bind=engine)


def migrate_proprietari_to_roles(db):
    """Migra i proprietari alla tabella soggetti_ruoli"""
    logger.info("Migrating proprietari to soggetti_ruoli...")

    # Ottieni il ruolo proprietario
    ruolo_query = text("""
        SELECT id FROM ruoli_disponibili
        WHERE codice = 'proprietario' AND modulo_id = 'affitti_lungo'
    """)
    ruolo_result = db.execute(ruolo_query).fetchone()

    if not ruolo_result:
        logger.error("Ruolo 'proprietario' non trovato! Eseguire prima la registrazione ruoli.")
        return 0

    ruolo_id = ruolo_result[0]

    # Migra i proprietari
    migrate_query = text("""
        INSERT INTO soggetti_ruoli (soggetto_id, ruolo_id, record_specializzazione_id, attivo, created_at)
        SELECT
            soggetto_id,
            :ruolo_id,
            id as record_specializzazione_id,
            TRUE as attivo,
            created_at
        FROM proprietari
        WHERE soggetto_id IS NOT NULL
        ON CONFLICT (soggetto_id, ruolo_id, record_specializzazione_id) DO NOTHING
    """)

    result = db.execute(migrate_query, {"ruolo_id": ruolo_id})
    count = result.rowcount
    db.commit()

    logger.info(f"✅ Migrati {count} proprietari")
    return count


def migrate_affittuari_to_roles(db):
    """Migra gli affittuari alla tabella soggetti_ruoli"""
    logger.info("Migrating affittuari to soggetti_ruoli...")

    # Ottieni il ruolo affittuario
    ruolo_query = text("""
        SELECT id FROM ruoli_disponibili
        WHERE codice = 'affittuario' AND modulo_id = 'affitti_lungo'
    """)
    ruolo_result = db.execute(ruolo_query).fetchone()

    if not ruolo_result:
        logger.error("Ruolo 'affittuario' non trovato!")
        return 0

    ruolo_id = ruolo_result[0]

    # Migra gli affittuari
    migrate_query = text("""
        INSERT INTO soggetti_ruoli (soggetto_id, ruolo_id, record_specializzazione_id, attivo, created_at)
        SELECT
            soggetto_id,
            :ruolo_id,
            id as record_specializzazione_id,
            TRUE as attivo,
            created_at
        FROM affittuari
        WHERE soggetto_id IS NOT NULL
        ON CONFLICT (soggetto_id, ruolo_id, record_specializzazione_id) DO NOTHING
    """)

    result = db.execute(migrate_query, {"ruolo_id": ruolo_id})
    count = result.rowcount
    db.commit()

    logger.info(f"✅ Migrati {count} affittuari")
    return count


def migrate_tecnici_to_roles(db):
    """Migra i tecnici alla tabella soggetti_ruoli"""
    logger.info("Migrating tecnici to soggetti_ruoli...")

    # Ottieni il ruolo tecnico
    ruolo_query = text("""
        SELECT id FROM ruoli_disponibili
        WHERE codice = 'tecnico' AND modulo_id = 'affitti_lungo'
    """)
    ruolo_result = db.execute(ruolo_query).fetchone()

    if not ruolo_result:
        logger.error("Ruolo 'tecnico' non trovato!")
        return 0

    ruolo_id = ruolo_result[0]

    # Migra i tecnici
    migrate_query = text("""
        INSERT INTO soggetti_ruoli (soggetto_id, ruolo_id, record_specializzazione_id, attivo, created_at)
        SELECT
            soggetto_id,
            :ruolo_id,
            id as record_specializzazione_id,
            TRUE as attivo,
            created_at
        FROM tecnici
        WHERE soggetto_id IS NOT NULL
        ON CONFLICT (soggetto_id, ruolo_id, record_specializzazione_id) DO NOTHING
    """)

    result = db.execute(migrate_query, {"ruolo_id": ruolo_id})
    count = result.rowcount
    db.commit()

    logger.info(f"✅ Migrati {count} tecnici")
    return count


def verify_migration(db):
    """Verifica la migrazione"""
    logger.info("\n" + "=" * 60)
    logger.info("VERIFICA MIGRAZIONE")
    logger.info("=" * 60)

    # Count soggetti con ruoli
    query = text("""
        SELECT
            COUNT(DISTINCT sr.soggetto_id) as soggetti_con_ruoli,
            COUNT(sr.id) as totale_assegnazioni,
            COUNT(DISTINCT CASE WHEN rd.codice = 'proprietario' THEN sr.soggetto_id END) as proprietari,
            COUNT(DISTINCT CASE WHEN rd.codice = 'affittuario' THEN sr.soggetto_id END) as affittuari,
            COUNT(DISTINCT CASE WHEN rd.codice = 'tecnico' THEN sr.soggetto_id END) as tecnici
        FROM soggetti_ruoli sr
        JOIN ruoli_disponibili rd ON sr.ruolo_id = rd.id
        WHERE sr.attivo = TRUE
    """)

    result = db.execute(query).fetchone()

    logger.info(f"\nSoggetti con almeno un ruolo: {result[0]}")
    logger.info(f"Totale assegnazioni ruoli: {result[1]}")
    logger.info(f"  - Proprietari: {result[2]}")
    logger.info(f"  - Affittuari: {result[3]}")
    logger.info(f"  - Tecnici: {result[4]}")

    # Soggetti con ruoli multipli
    multi_role_query = text("""
        SELECT
            COUNT(*) as soggetti_multi_ruolo
        FROM (
            SELECT soggetto_id
            FROM soggetti_ruoli
            WHERE attivo = TRUE
            GROUP BY soggetto_id
            HAVING COUNT(DISTINCT ruolo_id) > 1
        ) sub
    """)

    multi_result = db.execute(multi_role_query).fetchone()
    logger.info(f"\nSoggetti con ruoli multipli: {multi_result[0]}")

    # Esempi di soggetti con i loro ruoli
    examples_query = text("""
        SELECT
            s.id,
            COALESCE(s.ragione_sociale, s.nome || ' ' || s.cognome) as nome,
            STRING_AGG(rd.nome_display, ', ') as ruoli
        FROM soggetti_anagrafici s
        JOIN soggetti_ruoli sr ON s.id = sr.soggetto_id
        JOIN ruoli_disponibili rd ON sr.ruolo_id = rd.id
        WHERE sr.attivo = TRUE
        GROUP BY s.id, s.ragione_sociale, s.nome, s.cognome
        LIMIT 10
    """)

    examples = db.execute(examples_query).fetchall()

    logger.info("\nEsempi di soggetti con ruoli:")
    logger.info("-" * 60)
    for ex in examples:
        logger.info(f"ID {ex[0]}: {ex[1]} → {ex[2]}")

    logger.info("=" * 60 + "\n")


def main():
    """Esegui la migrazione"""
    logger.info("=" * 60)
    logger.info("MIGRAZIONE AL SISTEMA DI RUOLI DINAMICI")
    logger.info("=" * 60 + "\n")

    db = SessionLocal()

    try:
        # Migra ogni tipo di ruolo
        prop_count = migrate_proprietari_to_roles(db)
        aff_count = migrate_affittuari_to_roles(db)
        tec_count = migrate_tecnici_to_roles(db)

        total = prop_count + aff_count + tec_count

        logger.info(f"\n✅ MIGRAZIONE COMPLETATA")
        logger.info(f"Totale assegnazioni migrate: {total}")

        # Verifica
        verify_migration(db)

    except Exception as e:
        logger.error(f"❌ Errore durante la migrazione: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
