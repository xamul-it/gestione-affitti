"""
Script di migrazione per centralizzare i dati anagrafici.

Questo script:
1. Crea la tabella soggetti_anagrafici
2. Migra i dati da proprietari, affittuari, tecnici
3. Aggiunge le colonne soggetto_id alle tabelle esistenti
4. Mantiene i record originali per rollback

IMPORTANTE: Eseguire PRIMA di modificare i modelli SQLAlchemy
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from app.core.database import engine, SessionLocal
from app.core.models import SoggettoAnagrafico, TipoSoggetto
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_table_exists(table_name: str) -> bool:
    """Verifica se una tabella esiste nel database"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def create_soggetti_anagrafici_table():
    """Crea la tabella soggetti_anagrafici se non esiste"""
    logger.info("Creating soggetti_anagrafici table...")

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS soggetti_anagrafici (
                id SERIAL PRIMARY KEY,
                tipo_soggetto VARCHAR(20) NOT NULL,
                codice_fiscale VARCHAR(16) UNIQUE,
                partita_iva VARCHAR(11) UNIQUE,
                nome VARCHAR(100),
                cognome VARCHAR(100),
                data_nascita DATE,
                luogo_nascita VARCHAR(100),
                ragione_sociale VARCHAR(200),
                email VARCHAR(255),
                telefono VARCHAR(20),
                cellulare VARCHAR(20),
                pec VARCHAR(255),
                indirizzo VARCHAR(255),
                citta VARCHAR(100),
                cap VARCHAR(10),
                provincia VARCHAR(2),
                note VARCHAR(1000),
                attivo BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            );

            CREATE INDEX IF NOT EXISTS idx_soggetti_tipo ON soggetti_anagrafici(tipo_soggetto);
            CREATE INDEX IF NOT EXISTS idx_soggetti_cf ON soggetti_anagrafici(codice_fiscale);
            CREATE INDEX IF NOT EXISTS idx_soggetti_piva ON soggetti_anagrafici(partita_iva);
        """))

    logger.info("✅ Table soggetti_anagrafici created successfully")


def migrate_proprietari():
    """Migra i dati da proprietari a soggetti_anagrafici"""
    logger.info("Migrating proprietari to soggetti_anagrafici...")

    with engine.begin() as conn:
        # Count existing records
        result = conn.execute(text("SELECT COUNT(*) FROM proprietari"))
        count = result.scalar()
        logger.info(f"Found {count} proprietari to migrate")

        if count == 0:
            logger.info("No proprietari to migrate")
            return

        # Migrate data
        conn.execute(text("""
            INSERT INTO soggetti_anagrafici (
                tipo_soggetto, codice_fiscale, nome, cognome, data_nascita,
                luogo_nascita, email, telefono, cellulare, indirizzo,
                citta, cap, provincia, note, attivo, created_at, updated_at
            )
            SELECT
                'PERSONA_FISICA'::VARCHAR,
                codice_fiscale,
                nome,
                cognome,
                data_nascita::DATE,
                luogo_nascita,
                email,
                telefono,
                cellulare,
                indirizzo,
                citta,
                cap,
                provincia,
                note,
                attivo,
                created_at,
                updated_at
            FROM proprietari
            WHERE codice_fiscale NOT IN (
                SELECT codice_fiscale FROM soggetti_anagrafici WHERE codice_fiscale IS NOT NULL
            )
            ON CONFLICT (codice_fiscale) DO NOTHING;
        """))

        logger.info("✅ Proprietari migrated successfully")


def migrate_affittuari():
    """Migra i dati da affittuari a soggetti_anagrafici"""
    logger.info("Migrating affittuari to soggetti_anagrafici...")

    with engine.begin() as conn:
        # Count existing records
        result = conn.execute(text("SELECT COUNT(*) FROM affittuari"))
        count = result.scalar()
        logger.info(f"Found {count} affittuari to migrate")

        if count == 0:
            logger.info("No affittuari to migrate")
            return

        # Migrate data
        conn.execute(text("""
            INSERT INTO soggetti_anagrafici (
                tipo_soggetto, codice_fiscale, nome, cognome, data_nascita,
                luogo_nascita, email, telefono, cellulare, indirizzo,
                citta, cap, provincia, note, attivo, created_at, updated_at
            )
            SELECT
                'PERSONA_FISICA'::VARCHAR,
                codice_fiscale,
                nome,
                cognome,
                data_nascita,
                luogo_nascita,
                email,
                telefono,
                cellulare,
                indirizzo_residenza,
                citta_residenza,
                cap_residenza,
                provincia_residenza,
                note,
                TRUE,  -- affittuari non ha campo attivo
                created_at,
                updated_at
            FROM affittuari
            WHERE codice_fiscale NOT IN (
                SELECT codice_fiscale FROM soggetti_anagrafici WHERE codice_fiscale IS NOT NULL
            )
            ON CONFLICT (codice_fiscale) DO NOTHING;
        """))

        logger.info("✅ Affittuari migrated successfully")


def migrate_tecnici():
    """Migra i dati da tecnici a soggetti_anagrafici"""
    logger.info("Migrating tecnici to soggetti_anagrafici...")

    with engine.begin() as conn:
        # Count existing records
        result = conn.execute(text("SELECT COUNT(*) FROM tecnici"))
        count = result.scalar()
        logger.info(f"Found {count} tecnici to migrate")

        if count == 0:
            logger.info("No tecnici to migrate")
            return

        # Migrate data - tecnici possono essere persone fisiche o società
        conn.execute(text("""
            INSERT INTO soggetti_anagrafici (
                tipo_soggetto, codice_fiscale, partita_iva, nome, cognome,
                ragione_sociale, email, telefono, indirizzo, note,
                attivo, created_at
            )
            SELECT
                CASE
                    WHEN ragione_sociale IS NOT NULL AND ragione_sociale != ''
                    THEN 'PERSONA_GIURIDICA'::VARCHAR
                    ELSE 'PERSONA_FISICA'::VARCHAR
                END,
                codice_fiscale,
                partita_iva,
                nome,
                cognome,
                ragione_sociale,
                email,
                telefono,
                indirizzo,
                note,
                attivo,
                NOW()  -- tecnici non ha created_at
            FROM tecnici
            WHERE (codice_fiscale IS NOT NULL AND codice_fiscale NOT IN (
                SELECT codice_fiscale FROM soggetti_anagrafici WHERE codice_fiscale IS NOT NULL
            ))
            OR (partita_iva IS NOT NULL AND partita_iva NOT IN (
                SELECT partita_iva FROM soggetti_anagrafici WHERE partita_iva IS NOT NULL
            ))
            OR (codice_fiscale IS NULL AND partita_iva IS NULL);
        """))

        logger.info("✅ Tecnici migrated successfully")


def add_soggetto_id_columns():
    """Aggiunge le colonne soggetto_id alle tabelle esistenti"""
    logger.info("Adding soggetto_id columns...")

    with engine.begin() as conn:
        # Proprietari
        conn.execute(text("""
            ALTER TABLE proprietari
            ADD COLUMN IF NOT EXISTS soggetto_id INTEGER REFERENCES soggetti_anagrafici(id);

            CREATE INDEX IF NOT EXISTS idx_proprietari_soggetto ON proprietari(soggetto_id);
        """))

        # Affittuari
        conn.execute(text("""
            ALTER TABLE affittuari
            ADD COLUMN IF NOT EXISTS soggetto_id INTEGER REFERENCES soggetti_anagrafici(id);

            CREATE INDEX IF NOT EXISTS idx_affittuari_soggetto ON affittuari(soggetto_id);
        """))

        # Tecnici
        conn.execute(text("""
            ALTER TABLE tecnici
            ADD COLUMN IF NOT EXISTS soggetto_id INTEGER REFERENCES soggetti_anagrafici(id);

            CREATE INDEX IF NOT EXISTS idx_tecnici_soggetto ON tecnici(soggetto_id);
        """))

    logger.info("✅ soggetto_id columns added successfully")


def link_proprietari_to_soggetti():
    """Collega i record di proprietari ai soggetti_anagrafici"""
    logger.info("Linking proprietari to soggetti_anagrafici...")

    with engine.begin() as conn:
        result = conn.execute(text("""
            UPDATE proprietari p
            SET soggetto_id = s.id
            FROM soggetti_anagrafici s
            WHERE p.codice_fiscale = s.codice_fiscale
            AND p.soggetto_id IS NULL;
        """))

        logger.info(f"✅ Linked {result.rowcount} proprietari to soggetti_anagrafici")


def link_affittuari_to_soggetti():
    """Collega i record di affittuari ai soggetti_anagrafici"""
    logger.info("Linking affittuari to soggetti_anagrafici...")

    with engine.begin() as conn:
        result = conn.execute(text("""
            UPDATE affittuari a
            SET soggetto_id = s.id
            FROM soggetti_anagrafici s
            WHERE a.codice_fiscale = s.codice_fiscale
            AND a.soggetto_id IS NULL;
        """))

        logger.info(f"✅ Linked {result.rowcount} affittuari to soggetti_anagrafici")


def link_tecnici_to_soggetti():
    """Collega i record di tecnici ai soggetti_anagrafici"""
    logger.info("Linking tecnici to soggetti_anagrafici...")

    with engine.begin() as conn:
        # Link by codice_fiscale first
        result1 = conn.execute(text("""
            UPDATE tecnici t
            SET soggetto_id = s.id
            FROM soggetti_anagrafici s
            WHERE t.codice_fiscale = s.codice_fiscale
            AND t.codice_fiscale IS NOT NULL
            AND t.soggetto_id IS NULL;
        """))

        # Then link by partita_iva
        result2 = conn.execute(text("""
            UPDATE tecnici t
            SET soggetto_id = s.id
            FROM soggetti_anagrafici s
            WHERE t.partita_iva = s.partita_iva
            AND t.partita_iva IS NOT NULL
            AND t.soggetto_id IS NULL;
        """))

        total = result1.rowcount + result2.rowcount
        logger.info(f"✅ Linked {total} tecnici to soggetti_anagrafici")


def verify_migration():
    """Verifica che la migrazione sia andata a buon fine"""
    logger.info("\n=== Verification ===")

    with engine.begin() as conn:
        # Count soggetti
        result = conn.execute(text("SELECT COUNT(*) FROM soggetti_anagrafici"))
        soggetti_count = result.scalar()
        logger.info(f"Total soggetti_anagrafici: {soggetti_count}")

        # Count linked proprietari
        result = conn.execute(text("SELECT COUNT(*) FROM proprietari WHERE soggetto_id IS NOT NULL"))
        prop_linked = result.scalar()
        result = conn.execute(text("SELECT COUNT(*) FROM proprietari"))
        prop_total = result.scalar()
        logger.info(f"Proprietari linked: {prop_linked}/{prop_total}")

        # Count linked affittuari
        result = conn.execute(text("SELECT COUNT(*) FROM affittuari WHERE soggetto_id IS NOT NULL"))
        aff_linked = result.scalar()
        result = conn.execute(text("SELECT COUNT(*) FROM affittuari"))
        aff_total = result.scalar()
        logger.info(f"Affittuari linked: {aff_linked}/{aff_total}")

        # Count linked tecnici
        result = conn.execute(text("SELECT COUNT(*) FROM tecnici WHERE soggetto_id IS NOT NULL"))
        tec_linked = result.scalar()
        result = conn.execute(text("SELECT COUNT(*) FROM tecnici"))
        tec_total = result.scalar()
        logger.info(f"Tecnici linked: {tec_linked}/{tec_total}")

        # Check for multi-role subjects
        result = conn.execute(text("""
            SELECT
                s.id,
                COALESCE(s.ragione_sociale, CONCAT(s.nome, ' ', s.cognome)) as nome_display,
                COUNT(DISTINCT role) as role_count
            FROM soggetti_anagrafici s
            LEFT JOIN (
                SELECT soggetto_id, 'proprietario' as role FROM proprietari WHERE soggetto_id IS NOT NULL
                UNION ALL
                SELECT soggetto_id, 'affittuario' as role FROM affittuari WHERE soggetto_id IS NOT NULL
                UNION ALL
                SELECT soggetto_id, 'tecnico' as role FROM tecnici WHERE soggetto_id IS NOT NULL
            ) roles ON s.id = roles.soggetto_id
            GROUP BY s.id, s.ragione_sociale, s.nome, s.cognome
            HAVING COUNT(DISTINCT role) > 1;
        """))

        multi_role = result.fetchall()
        if multi_role:
            logger.info(f"\n✨ Found {len(multi_role)} subjects with multiple roles:")
            for subject in multi_role:
                logger.info(f"  - {subject[1]} (ID: {subject[0]}) has {subject[2]} roles")
        else:
            logger.info("\nNo subjects with multiple roles found")


def main():
    """Esegue la migrazione completa"""
    logger.info("=" * 60)
    logger.info("MIGRATION: Centralizing anagrafica to soggetti_anagrafici")
    logger.info("=" * 60)

    try:
        # Step 1: Create soggetti_anagrafici table
        create_soggetti_anagrafici_table()

        # Step 2: Migrate data from existing tables
        migrate_proprietari()
        migrate_affittuari()
        migrate_tecnici()

        # Step 3: Add soggetto_id columns
        add_soggetto_id_columns()

        # Step 4: Link existing records to soggetti
        link_proprietari_to_soggetti()
        link_affittuari_to_soggetti()
        link_tecnici_to_soggetti()

        # Step 5: Verify migration
        verify_migration()

        logger.info("\n" + "=" * 60)
        logger.info("✅ MIGRATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info("\nNext steps:")
        logger.info("1. Verify the data in soggetti_anagrafici table")
        logger.info("2. Update SQLAlchemy models to use soggetto_id")
        logger.info("3. Update API schemas and routes")
        logger.info("4. Update frontend to use new structure")

    except Exception as e:
        logger.error(f"\n❌ MIGRATION FAILED: {e}")
        logger.error("The database should still be in a consistent state.")
        logger.error("You can re-run this script to retry the migration.")
        raise


if __name__ == "__main__":
    main()
