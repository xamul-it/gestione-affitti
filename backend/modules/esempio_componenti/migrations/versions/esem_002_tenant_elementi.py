"""Tenant table elementi_esempio

Revision ID: esem_002
Revises: esem_001
Create Date: 2026-11-25

esem_001 created only the public domain tables: in every tenant the table
existed only because the installer falls back to the SQLAlchemy metadata
when a manifest table is missing (found by scripts/tenant_prova.py).
IF NOT EXISTS: tenants created that way keep their table and rows.
Same columns as models/elemento_esempio.py.
"""
from alembic import op, context
from sqlalchemy import text

revision = "esem_002"
down_revision = "esem_001"
branch_labels = None
depends_on = None

target_schema = "tenant"


def upgrade():
    schema = context.get_x_argument(as_dictionary=True).get("schema")
    if not schema or schema == "public":
        return
    conn = op.get_bind()
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS elementi_esempio (
            id SERIAL PRIMARY KEY,
            codice VARCHAR(20) NOT NULL,
            titolo VARCHAR(200) NOT NULL,
            descrizione TEXT,
            categoria_id INTEGER REFERENCES public.esem_categorie_esempio(id),
            priorita_id INTEGER REFERENCES public.esem_priorita_esempio(id),
            quantita INTEGER,
            importo NUMERIC(10, 2),
            percentuale NUMERIC(5, 2),
            data_inizio DATE,
            data_fine DATE,
            stato VARCHAR(20) NOT NULL,
            attivo BOOLEAN NOT NULL,
            note TEXT,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_elementi_esempio_codice ON elementi_esempio (codice)"))


def downgrade():
    pass
