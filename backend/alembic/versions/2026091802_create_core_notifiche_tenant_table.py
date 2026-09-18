"""Create core_notifiche inside every tenant schema.

Revision ID: 2026091802
Revises: 2026091801
Create Date: 2026-09-18
"""
from alembic import op
import sqlalchemy as sa

revision = "2026091802"
down_revision = "2026091801"
branch_labels = None
depends_on = None

target_schema = "tenant"


def upgrade() -> None:
    op.create_table(
        "core_notifiche",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.ForeignKeyConstraint(["user_id"], ["core_users.id"], ondelete="CASCADE"),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=100), nullable=False),
        sa.Column("titolo", sa.String(length=255), nullable=False),
        sa.Column("corpo", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("link_url", sa.String(length=500), nullable=True),
        sa.Column("canali", sa.String(length=20), nullable=False),
        sa.Column("stato_email", sa.String(length=20), nullable=False),
        sa.Column("errore_email", sa.Text(), nullable=True),
        sa.Column("letta", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("letta_il", sa.DateTime(), nullable=True),
        sa.Column("creata_il", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_core_notifiche_id", "core_notifiche", ["id"])
    op.create_index("idx_core_notifiche_user_letta", "core_notifiche", ["user_id", "letta"])
    op.create_index("idx_core_notifiche_tipo", "core_notifiche", ["tipo"])


def downgrade() -> None:
    op.drop_table("core_notifiche")
