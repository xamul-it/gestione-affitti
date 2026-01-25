"""
Create immobili public domain tables.
"""
from alembic import op, context
from sqlalchemy import MetaData
from app.core.database import Base

import sys
from pathlib import Path

modules_dir = Path(__file__).resolve().parents[2]
if str(modules_dir) not in sys.path:
    sys.path.insert(0, str(modules_dir))

import importlib

for module_name in [
    "immobili.models.categoria_catastale",
    "immobili.models.tipologia_terreno",
]:
    importlib.import_module(module_name)

# Revision identifiers, used by Alembic.
revision = "2025022001_public_domain"
down_revision = "2025021702_baseline"
branch_labels = None
depends_on = None

target_schema = "public"

PUBLIC_TABLES = {
    "immo_categorie_catastali",
    "immo_tipologie_terreno",
}


def _get_target_schema():
    return context.get_x_argument(as_dictionary=True).get("schema")


def _get_public_tables():
    target_metadata = MetaData()
    for table in Base.metadata.tables.values():
        if table.name in PUBLIC_TABLES:
            table.to_metadata(target_metadata, schema="public")
    return list(target_metadata.sorted_tables)


def upgrade():
    schema = _get_target_schema()
    if schema and schema != "public":
        return
    bind = op.get_bind()
    for table in _get_public_tables():
        table.create(bind=bind, checkfirst=True)


def downgrade():
    schema = _get_target_schema()
    if schema and schema != "public":
        return
    bind = op.get_bind()
    for table in reversed(_get_public_tables()):
        table.drop(bind=bind, checkfirst=True)
