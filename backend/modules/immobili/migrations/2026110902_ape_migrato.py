"""Remember which old energy certificate became which APE document.

immo_certificati_energetici is kept read-only after the move to core APE
documents (immobili.post_sync -> migra_ape). migrato_documento_id marks a row
as migrated for good, so an APE document the user later deletes is not
re-created from the old row at the next promote. Add-column only.
"""
from alembic import op, context
from sqlalchemy import text

revision = "2026110902_ape_migrato"
down_revision = "2026110901_variazioni_catastali"
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
        DO $mig$ BEGIN
            IF to_regclass('immo_certificati_energetici') IS NOT NULL THEN
                ALTER TABLE immo_certificati_energetici ADD COLUMN IF NOT EXISTS migrato_documento_id INTEGER;
            END IF;
        END $mig$;
    """))


def downgrade():
    pass
