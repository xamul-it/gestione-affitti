"""Create core_scadenze/core_scadenza_destinatari/core_scadenza_log inside
every tenant schema.

These tables were previously only ever created in `public` (via
create_core_tables()'s unconditional Base.metadata.create_all()), meaning
every tenant shared a single, non-isolated scadenzario. Verified against
the live database: 0 rows in all three tables in every environment, so
this is a purely structural fix, no data migration needed.

Revision ID: 2026091801
Revises: 2026072301
Create Date: 2026-09-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "2026091801"
down_revision = "2026072301"
branch_labels = None
depends_on = None

target_schema = "tenant"


def upgrade() -> None:
    bind = op.get_bind()

    priorita_enum = postgresql.ENUM(
        "BASSA", "MEDIA", "ALTA", name="prioritascadenza", create_type=True
    )
    priorita_enum.create(bind, checkfirst=True)

    stato_enum = postgresql.ENUM(
        "ATTIVA", "SCADUTA", "COMPLETATA", "POSTICIPATA", "CANCELLATA",
        name="statoscadenza", create_type=True
    )
    stato_enum.create(bind, checkfirst=True)

    op.create_table(
        "core_scadenze",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("modulo", sa.String(length=100), nullable=True),
        sa.Column("entity_type", sa.String(length=100), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("titolo", sa.String(length=200), nullable=False),
        sa.Column("descrizione", sa.Text(), nullable=True),
        sa.Column("data_scadenza", sa.Date(), nullable=False),
        sa.Column("priorita", priorita_enum, nullable=False),
        sa.Column("stato", stato_enum, nullable=False),
        # Unqualified "core_users.id" resolves via the tenant migration's
        # active search_path (tenant_schema, public) to public.core_users,
        # which is never replicated per-tenant. Same mechanism already
        # proven by every business module's tenant migration (e.g.
        # affitti_lungo) that references public domain tables.
        sa.ForeignKeyConstraint(["creato_da"], ["core_users.id"], ondelete="CASCADE"),
        sa.Column("creato_da", sa.Integer(), nullable=False),
        sa.Column("creato_il", sa.DateTime(), nullable=False),
        sa.Column("modificato_il", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["completato_da"], ["core_users.id"], ondelete="SET NULL"),
        sa.Column("completato_da", sa.Integer(), nullable=True),
        sa.Column("completato_il", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_core_scadenze_id", "core_scadenze", ["id"])
    op.create_index("ix_core_scadenze_data_scadenza", "core_scadenze", ["data_scadenza"])
    op.create_index("ix_core_scadenze_stato", "core_scadenze", ["stato"])
    op.create_index("idx_core_scadenze_creator", "core_scadenze", ["creato_da"])
    op.create_index("idx_core_scadenze_entity", "core_scadenze", ["modulo", "entity_type", "entity_id"])
    op.create_index("idx_core_scadenze_stato_data", "core_scadenze", ["stato", "data_scadenza"])

    op.create_table(
        "core_scadenza_destinatari",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.ForeignKeyConstraint(["scadenza_id"], ["core_scadenze.id"], ondelete="CASCADE"),
        sa.Column("scadenza_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["core_users.id"], ondelete="CASCADE"),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("notificato", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notificato_il", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("scadenza_id", "user_id", name="uq_scadenza_user"),
    )
    op.create_index("ix_core_scadenza_destinatari_id", "core_scadenza_destinatari", ["id"])
    op.create_index("idx_core_destinatari_scadenza", "core_scadenza_destinatari", ["scadenza_id"])
    op.create_index("idx_core_destinatari_user", "core_scadenza_destinatari", ["user_id"])
    op.create_index("idx_core_destinatari_notificato", "core_scadenza_destinatari", ["notificato"])

    op.create_table(
        "core_scadenza_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.ForeignKeyConstraint(["scadenza_id"], ["core_scadenze.id"], ondelete="CASCADE"),
        sa.Column("scadenza_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["core_users.id"], ondelete="SET NULL"),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("azione", sa.String(length=50), nullable=False),
        sa.Column("campo_modificato", sa.String(length=100), nullable=True),
        sa.Column("valore_precedente", sa.Text(), nullable=True),
        sa.Column("valore_nuovo", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
    )
    op.create_index("ix_core_scadenza_log_id", "core_scadenza_log", ["id"])
    op.create_index("ix_core_scadenza_log_timestamp", "core_scadenza_log", ["timestamp"])
    op.create_index("idx_core_log_scadenza", "core_scadenza_log", ["scadenza_id"])
    op.create_index("idx_core_log_azione", "core_scadenza_log", ["azione"])


def downgrade() -> None:
    op.drop_table("core_scadenza_log")
    op.drop_table("core_scadenza_destinatari")
    op.drop_table("core_scadenze")
    bind = op.get_bind()
    postgresql.ENUM(name="statoscadenza").drop(bind, checkfirst=True)
    postgresql.ENUM(name="prioritascadenza").drop(bind, checkfirst=True)
