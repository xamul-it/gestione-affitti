"""Catastal changes log (immo_variazioni_catastali), tenant table.

Raw SQL for the same reason as 2026092301_conduttori_spese (env.py module
prefixing would mangle op.create_table names).
"""
from alembic import op, context
from sqlalchemy import text

revision = "2026110901_variazioni_catastali"
down_revision = "2026092301_conduttori_spese"
branch_labels = None
depends_on = None

target_schema = "tenant"


def _get_target_schema():
    return context.get_x_argument(as_dictionary=True).get("schema")


def upgrade():
    schema = _get_target_schema()
    if not schema or schema == "public":
        return
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS immo_variazioni_catastali (
            id SERIAL PRIMARY KEY,
            unita_immobiliare_id INTEGER NOT NULL REFERENCES immo_unita_immobiliari(id) ON DELETE CASCADE,
            documento_id INTEGER,
            origine VARCHAR(20) NOT NULL,
            campo VARCHAR(50) NOT NULL,
            valore_precedente TEXT,
            valore_nuovo TEXT,
            data_riferimento DATE NOT NULL,
            utente_id INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_immo_variazioni_catastali_unita ON immo_variazioni_catastali(unita_immobiliare_id)"
    ))


def downgrade():
    schema = _get_target_schema()
    if not schema or schema == "public":
        return
    op.execute(text("DROP TABLE IF EXISTS immo_variazioni_catastali"))
