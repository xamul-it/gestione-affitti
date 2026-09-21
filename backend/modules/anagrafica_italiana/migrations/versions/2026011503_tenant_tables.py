"""anagrafica tenant tables

Revision ID: 2026011503_tenant_tables
Revises: 2026011502_public_domain
Create Date: 2026-01-15

NOTE (2026-09-21): the FK targets for the two document-override tables
below were updated from public.anag_tipi_documento/anag_stati_documento to
public.core_tipi_documento/core_stati_documento, because those tables were
renamed (main chain migration 2026092101) when the document registry
became a core platform service. This migration itself keeps creating
anag_tipi_documento_overrides/anag_stati_documento_overrides under their
original names — later migrations in this module's own chain
(2026013101_documento_multifile.py and others) still reference
anag_documenti/anag_documenti_files by name, so renaming here would break
them. The main chain's 2026092102 migration performs the actual rename to
core_tipi_documento_overrides/core_stati_documento_overrides for every
tenant, including ones that reach this point in anagrafica's chain after
the rename already happened elsewhere (its rename is defensive: a no-op
if the old name doesn't exist yet, or the new name already does).
Editing this file only affects tenants that haven't reached this revision
yet (i.e. brand new ones) — every existing tenant's alembic_version_anag
is already past it and will never re-run it.
"""

from alembic import op, context
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "2026011503_tenant_tables"
down_revision = "2026011502_public_domain"
branch_labels = None
depends_on = None

# Run only in tenant schemas
target_schema = "tenant"


def upgrade() -> None:
    schema = context.get_x_argument(as_dictionary=True).get("schema")
    if not schema or schema == "public":
        return
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS anag_soggetti_anagrafici (
            id SERIAL PRIMARY KEY,
            tipo_soggetto VARCHAR(50) NOT NULL,
            user_id INTEGER UNIQUE,
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
            attivo BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ,
            CONSTRAINT fk_soggetti_user FOREIGN KEY(user_id) REFERENCES public.core_users(id)
        )
    """))

    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_soggetti_tipo ON anag_soggetti_anagrafici(tipo_soggetto)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_soggetti_codice_fiscale ON anag_soggetti_anagrafici(codice_fiscale)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_soggetti_partita_iva ON anag_soggetti_anagrafici(partita_iva)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_soggetti_user_id ON anag_soggetti_anagrafici(user_id)"))

    op.execute(text("""
        CREATE TABLE IF NOT EXISTS anag_ruoli_azienda (
            id SERIAL PRIMARY KEY,
            persona_fisica_id INTEGER NOT NULL REFERENCES anag_soggetti_anagrafici(id) ON DELETE CASCADE,
            persona_giuridica_id INTEGER NOT NULL REFERENCES anag_soggetti_anagrafici(id) ON DELETE CASCADE,
            ruolo_tipo_id INTEGER REFERENCES public.anag_ruoli_azienda_tipi(id) ON DELETE SET NULL,
            ruolo VARCHAR(100),
            data_inizio DATE,
            data_fine DATE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ
        )
    """))

    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_ruoli_azienda_persona_fisica ON anag_ruoli_azienda(persona_fisica_id)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_ruoli_azienda_persona_giuridica ON anag_ruoli_azienda(persona_giuridica_id)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_ruoli_azienda_ruolo_tipo ON anag_ruoli_azienda(ruolo_tipo_id)"))

    op.execute(text("""
        CREATE TABLE IF NOT EXISTS anag_tipi_documento_overrides (
            id SERIAL PRIMARY KEY,
            tipo_documento_id INTEGER NOT NULL REFERENCES public.core_tipi_documento(id) ON DELETE CASCADE,
            codice VARCHAR(50),
            nome VARCHAR(100),
            descrizione VARCHAR(255),
            categoria VARCHAR(50),
            richiede_scadenza BOOLEAN,
            attivo BOOLEAN,
            is_deleted BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ,
            UNIQUE(tipo_documento_id)
        )
    """))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_tipi_doc_overrides_tipo ON anag_tipi_documento_overrides(tipo_documento_id)"))

    op.execute(text("""
        CREATE TABLE IF NOT EXISTS anag_stati_documento_overrides (
            id SERIAL PRIMARY KEY,
            stato_documento_id INTEGER NOT NULL REFERENCES public.core_stati_documento(id) ON DELETE CASCADE,
            codice VARCHAR(20),
            nome VARCHAR(100),
            descrizione VARCHAR(255),
            attivo BOOLEAN,
            is_deleted BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ,
            UNIQUE(stato_documento_id)
        )
    """))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_stati_doc_overrides_stato ON anag_stati_documento_overrides(stato_documento_id)"))

    op.execute(text("""
        CREATE TABLE IF NOT EXISTS anag_comuni_italia_overrides (
            id SERIAL PRIMARY KEY,
            comune_id INTEGER NOT NULL REFERENCES public.anag_comuni_italia(id) ON DELETE CASCADE,
            nome VARCHAR(100),
            nome_normalized VARCHAR(100),
            codice_istat VARCHAR(10),
            codice_catastale VARCHAR(10),
            cap VARCHAR(10),
            provincia_sigla VARCHAR(2),
            provincia_nome VARCHAR(100),
            regione VARCHAR(100),
            latitudine NUMERIC(10, 7),
            longitudine NUMERIC(10, 7),
            is_deleted BOOLEAN NOT NULL DEFAULT false,
            deleted_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ,
            UNIQUE(comune_id)
        )
    """))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_comuni_overrides_comune ON anag_comuni_italia_overrides(comune_id)"))

    op.execute(text("""
        CREATE TABLE IF NOT EXISTS anag_ruoli_azienda_tipi_overrides (
            id SERIAL PRIMARY KEY,
            ruolo_tipo_id INTEGER NOT NULL REFERENCES public.anag_ruoli_azienda_tipi(id) ON DELETE CASCADE,
            nome VARCHAR(100),
            descrizione VARCHAR(500),
            attivo BOOLEAN,
            is_deleted BOOLEAN NOT NULL DEFAULT false,
            deleted_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ,
            UNIQUE(ruolo_tipo_id)
        )
    """))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_ruoli_overrides_ruolo ON anag_ruoli_azienda_tipi_overrides(ruolo_tipo_id)"))


def downgrade() -> None:
    schema = context.get_x_argument(as_dictionary=True).get("schema")
    if not schema or schema == "public":
        return
    op.execute(text("DROP TABLE IF EXISTS anag_ruoli_azienda_tipi_overrides CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS anag_comuni_italia_overrides CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS anag_stati_documento_overrides CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS anag_tipi_documento_overrides CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS anag_ruoli_azienda CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS anag_soggetti_anagrafici CASCADE"))
