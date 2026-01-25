"""repair anagrafica public domain tables

Revision ID: 2026011504_public_domain_fix
Revises: 2026011503_tenant_tables
Create Date: 2026-01-20
"""

from alembic import op, context
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "2026011504_public_domain_fix"
down_revision = "2026011503_tenant_tables"
branch_labels = None
depends_on = None

# Run only in public schema
target_schema = "public"


def upgrade() -> None:
    schema = context.get_x_argument(as_dictionary=True).get("schema")
    if schema != "public":
        return

    op.execute(text("""
        CREATE TABLE IF NOT EXISTS public.anag_tipi_documento (
            id SERIAL PRIMARY KEY,
            codice VARCHAR(50) NOT NULL UNIQUE,
            nome VARCHAR(100) NOT NULL,
            descrizione VARCHAR(255),
            categoria VARCHAR(50),
            richiede_scadenza BOOLEAN DEFAULT false,
            attivo BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ
        )
    """))

    op.execute(text("""
        CREATE TABLE IF NOT EXISTS public.anag_stati_documento (
            id SERIAL PRIMARY KEY,
            codice VARCHAR(20) NOT NULL UNIQUE,
            nome VARCHAR(100) NOT NULL,
            descrizione VARCHAR(255),
            attivo BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ
        )
    """))

    op.execute(text("""
        CREATE TABLE IF NOT EXISTS public.anag_comuni_italia (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            nome_normalized VARCHAR(100),
            codice_istat VARCHAR(10) UNIQUE,
            codice_catastale VARCHAR(10) UNIQUE,
            cap VARCHAR(10),
            provincia_sigla VARCHAR(2),
            provincia_nome VARCHAR(100),
            regione VARCHAR(100),
            latitudine NUMERIC(10, 7),
            longitudine NUMERIC(10, 7),
            attivo BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ
        )
    """))

    op.execute(text("""
        CREATE TABLE IF NOT EXISTS public.anag_ruoli_azienda_tipi (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL UNIQUE,
            descrizione VARCHAR(500),
            attivo BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ
        )
    """))

    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_tipi_documento_codice ON public.anag_tipi_documento(codice)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_tipi_documento_categoria ON public.anag_tipi_documento(categoria)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_stati_documento_codice ON public.anag_stati_documento(codice)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_comuni_italia_nome ON public.anag_comuni_italia(nome)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_comuni_italia_provincia ON public.anag_comuni_italia(provincia_sigla)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_ruoli_azienda_tipi_nome ON public.anag_ruoli_azienda_tipi(nome)"))


def downgrade() -> None:
    schema = context.get_x_argument(as_dictionary=True).get("schema")
    if schema != "public":
        return
    # No destructive downgrade for domain data
    pass
