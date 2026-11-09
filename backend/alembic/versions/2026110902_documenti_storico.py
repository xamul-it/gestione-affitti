"""History columns on the tenant core_documenti table.

- data_riferimento: the date the document refers to (not the upload date);
- stato CORRENTE/SOSTITUITO + sostituito_da_id: for SOSTITUTIVO document
  types a newer document supersedes the previous one, which stays as history;
- sottotipo, dati (validated form data), scadenza_id (linked core_scadenze).

Add-column only, then a backfill of legacy rows (see backfill()). Guarded by
to_regclass: a tenant without core_documenti (module not installed yet) is
skipped, and the model creates the table with these columns later.

Revision ID: 2026110902
Revises: 2026110901
Create Date: 2026-11-09
"""
from alembic import op
import sqlalchemy as sa

revision = "2026110902"
down_revision = "2026110901"
branch_labels = None
depends_on = None

target_schema = "tenant"

_COLUMNS = (
    ("data_riferimento", "DATE"),
    ("stato", "VARCHAR(20) NOT NULL DEFAULT 'CORRENTE'"),
    ("sostituito_da_id", "INTEGER REFERENCES core_documenti(id) ON DELETE SET NULL"),
    ("sottotipo", "VARCHAR(50)"),
    ("dati", "JSON"),
    ("scadenza_id", "INTEGER REFERENCES core_scadenze(id) ON DELETE SET NULL"),
)

BACKFILL_SQL = """
UPDATE core_documenti d SET tipo_documento_id = t.id
  FROM public.core_tipi_documento t
 WHERE d.tipo_documento_id IS NULL AND d.tipo_documento IS NOT NULL
   AND t.codice = d.tipo_documento::text;
UPDATE core_documenti SET stato = 'CORRENTE' WHERE stato IS NULL;
UPDATE core_documenti
   SET data_riferimento = COALESCE(
         CASE WHEN (metadata_parsato->>'data_visura') ~ '^\\d{4}-\\d{2}-\\d{2}$'
              THEN (metadata_parsato->>'data_visura')::date END,
         created_at::date)
 WHERE data_riferimento IS NULL;
"""


def backfill(conn) -> None:
    for statement in BACKFILL_SQL.split(";"):
        if statement.strip():
            conn.execute(sa.text(statement))


def upgrade() -> None:
    adds = "\n".join(
        f"ALTER TABLE core_documenti ADD COLUMN IF NOT EXISTS {name} {ddl};" for name, ddl in _COLUMNS
    )
    op.execute(sa.text(f"""
        DO $mig$
        BEGIN
            IF to_regclass('core_documenti') IS NOT NULL THEN
                IF to_regclass('core_scadenze') IS NULL THEN
                    RAISE EXCEPTION 'core_scadenze missing in this schema';
                END IF;
                {adds}
                CREATE INDEX IF NOT EXISTS ix_core_documenti_stato ON core_documenti (stato);
                {BACKFILL_SQL}
            END IF;
        END $mig$;
    """))


def downgrade() -> None:
    for name, _ in reversed(_COLUMNS):
        op.execute(sa.text(f"""
            DO $mig$ BEGIN
                IF to_regclass('core_documenti') IS NOT NULL THEN
                    ALTER TABLE core_documenti DROP COLUMN IF EXISTS {name};
                END IF;
            END $mig$;
        """))
