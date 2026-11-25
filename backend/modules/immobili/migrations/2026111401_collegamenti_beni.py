"""Links between beni: pertinenze, buildings on a parcel, parcels of a farm.

Phase 2b of docs/superpowers/specs/2026-11-10-beni-catastali-design.md.
Adds one table, no data is touched. The link type has no CHECK: the list
lives in Python (services/collegamenti_beni.TIPI_COLLEGAMENTO).
"""
from alembic import op, context
from sqlalchemy import text

revision = "2026111401_collegamenti_beni"
down_revision = "2026111301_terreni_beni"
branch_labels = None
depends_on = None

target_schema = "tenant"


def crea_collegamenti(conn) -> None:
    """Table and indexes, idempotent; same columns as models/collegamento_beni.py."""
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS immo_beni_collegamenti (
            id SERIAL PRIMARY KEY,
            bene_id INTEGER NOT NULL REFERENCES immo_beni(id) ON DELETE CASCADE,
            bene_collegato_id INTEGER NOT NULL REFERENCES immo_beni(id) ON DELETE CASCADE,
            tipo VARCHAR(30) NOT NULL,
            data_inizio DATE,
            data_fine DATE,
            note TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ,
            CONSTRAINT immo_beni_collegamenti_non_se_stesso CHECK (bene_id <> bene_collegato_id),
            CONSTRAINT immo_beni_collegamenti_date CHECK (
                data_fine IS NULL OR data_inizio IS NULL OR data_fine >= data_inizio)
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_immo_beni_collegamenti_bene_id "
        "ON immo_beni_collegamenti (bene_id)"))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_immo_beni_collegamenti_bene_collegato_id "
        "ON immo_beni_collegamenti (bene_collegato_id)"))
    conn.execute(text(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_immo_beni_collegamenti_aperto "
        "ON immo_beni_collegamenti (bene_id, bene_collegato_id, tipo) WHERE data_fine IS NULL"))
    conn.execute(text(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_immo_beni_pertinenza_aperta "
        "ON immo_beni_collegamenti (bene_collegato_id) "
        "WHERE tipo = 'PERTINENZA' AND data_fine IS NULL"))


def _get_target_schema():
    return context.get_x_argument(as_dictionary=True).get("schema")


def upgrade():
    schema = _get_target_schema()
    if not schema or schema == "public":
        return
    conn = op.get_bind()
    if not conn.execute(text("SELECT to_regclass('immo_beni') IS NOT NULL")).scalar():
        return
    crea_collegamenti(conn)


def downgrade():
    op.get_bind().execute(text("DROP TABLE IF EXISTS immo_beni_collegamenti"))
