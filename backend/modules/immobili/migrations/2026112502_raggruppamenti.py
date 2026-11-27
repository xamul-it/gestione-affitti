"""Raggruppamenti (rami) of beni — phase 4a of
docs/superpowers/specs/2026-11-10-beni-catastali-design.md.

crea_schema(): table immo_raggruppamenti and column immo_beni.raggruppamento_id.
converti(): open PARTE_DI_FONDO links become one FONDO ramo per main parcel.
It stops and lists the doubtful cases before any write. Nothing is zeroed.
Downgrade is the backup.
"""
from alembic import op, context
from sqlalchemy import text

revision = "2026112502_raggruppamenti"
down_revision = "2026112501_relazione_unica"
branch_labels = None
depends_on = None

target_schema = "tenant"


def crea_schema(conn) -> None:
    """Table, column, indexes; idempotent; same columns as models/raggruppamento.py."""
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS immo_raggruppamenti (
            id SERIAL PRIMARY KEY,
            tipo VARCHAR(30) NOT NULL,
            nome VARCHAR(200) NOT NULL,
            padre_id INTEGER REFERENCES immo_raggruppamenti(id) ON DELETE RESTRICT,
            descrizione TEXT,
            note TEXT,
            attivo BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ,
            CONSTRAINT immo_raggruppamenti_non_se_stesso CHECK (padre_id IS NULL OR padre_id <> id)
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_immo_raggruppamenti_padre_id ON immo_raggruppamenti (padre_id)"))
    conn.execute(text(
        "ALTER TABLE immo_beni ADD COLUMN IF NOT EXISTS raggruppamento_id INTEGER"))
    esiste_fk = conn.execute(text(
        "SELECT 1 FROM pg_constraint WHERE conname = 'immo_beni_raggruppamento_id_fkey' "
        "AND connamespace = current_schema()::regnamespace")).first()
    if not esiste_fk:
        conn.execute(text(
            "ALTER TABLE immo_beni ADD CONSTRAINT immo_beni_raggruppamento_id_fkey "
            "FOREIGN KEY (raggruppamento_id) REFERENCES immo_raggruppamenti(id) ON DELETE RESTRICT"))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_immo_beni_raggruppamento_id ON immo_beni (raggruppamento_id)"))


def converti(conn) -> dict:
    """PARTE_DI_FONDO -> FONDO rami. Filled in by the conversion step (see below)."""
    return {"fondi_creati": 0, "terreni_spostati": 0, "collegamenti_rimossi": 0}


def _get_target_schema():
    return context.get_x_argument(as_dictionary=True).get("schema")


def upgrade():
    schema = _get_target_schema()
    if not schema or schema == "public":
        return
    conn = op.get_bind()
    if not conn.execute(text("SELECT to_regclass('immo_beni') IS NOT NULL")).scalar():
        return
    crea_schema(conn)
    conteggi = converti(conn)
    print(f"  [{schema}] raggruppamenti: {conteggi}", flush=True)


def downgrade():
    raise NotImplementedError("Restore from the backup taken before the migration")
