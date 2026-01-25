"""
Create affitti_lungo tenant tables.
"""
from alembic import op, context
from sqlalchemy import MetaData
from app.core.database import Base

import affitti_lungo.models  # noqa: F401 - register models in Base metadata

# Revision identifiers, used by Alembic.
revision = "2025022001_tenant_tables"
down_revision = None
branch_labels = None
depends_on = None

target_schema = "tenant"

TENANT_TABLES = {
    "affittuari",
    "contratti",
    "incassi",
    "spese",
    "ripartizioni_spese",
    "tecnici",
}


def _get_target_schema():
    return context.get_x_argument(as_dictionary=True).get("schema")


def _get_tenant_tables(schema):
    target_metadata = MetaData()
    for table in Base.metadata.sorted_tables:
        if table.name in TENANT_TABLES:
            table.to_metadata(target_metadata, schema=schema)
    return list(target_metadata.sorted_tables)


def upgrade():
    schema = _get_target_schema()
    if not schema or schema == "public":
        return
    bind = op.get_bind()
    for table in _get_tenant_tables(schema):
        table.create(bind=bind, checkfirst=True)


def downgrade():
    schema = _get_target_schema()
    if not schema or schema == "public":
        return
    bind = op.get_bind()
    for table in reversed(_get_tenant_tables(schema)):
        table.drop(bind=bind, checkfirst=True)
