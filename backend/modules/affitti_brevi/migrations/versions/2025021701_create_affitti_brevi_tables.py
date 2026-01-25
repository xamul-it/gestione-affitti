"""
Create affitti_brevi tenant tables.
"""
from alembic import op, context
from sqlalchemy import MetaData, Table, Column, Integer
from app.core.database import Base

import importlib
import sys
from pathlib import Path

modules_dir = Path(__file__).resolve().parents[3]
if str(modules_dir) not in sys.path:
    sys.path.insert(0, str(modules_dir))

for module_name in [
    "affitti_brevi.models.canale",
    "affitti_brevi.models.calendario_canale",
    "affitti_brevi.models.prenotazione",
    "affitti_brevi.models.blocco_calendario",
    "affitti_brevi.models.soggiorno",
    "affitti_brevi.models.ospite_soggiorno",
    "affitti_brevi.models.tassa_soggiorno_config",
    "affitti_brevi.models.tassa_soggiorno_scaglione",
    "affitti_brevi.models.tassa_soggiorno",
    "affitti_brevi.models.comunicazione",
    "affitti_brevi.models.attivita_schedulata",
]:
    importlib.import_module(module_name)

# Revision identifiers, used by Alembic.
revision = "2025021701"
down_revision = None
branch_labels = None
depends_on = None

# Only run on tenant schemas
target_schema = "tenant"


def _get_target_schema():
    args = context.get_x_argument(as_dictionary=True)
    return args.get("schema")


def _get_affitti_brevi_tables(schema):
    target_metadata = MetaData()
    _ensure_fk_targets(target_metadata, schema)
    for table in Base.metadata.tables.values():
        if table.name.startswith("ab_"):
            table.to_metadata(target_metadata, schema=schema)
    return list(target_metadata.tables.values())


def _ensure_fk_targets(target_metadata: MetaData, schema: str) -> None:
    # External FK targets referenced by affitti_brevi tables.
    Table(
        "immo_unita_immobiliari",
        target_metadata,
        Column("id", Integer, primary_key=True),
        schema=schema,
    )
    Table(
        "anag_soggetti_anagrafici",
        target_metadata,
        Column("id", Integer, primary_key=True),
        schema=schema,
    )
    Table(
        "anag_comuni_italia",
        target_metadata,
        Column("id", Integer, primary_key=True),
        schema="public",
    )


def upgrade():
    bind = op.get_bind()
    schema = _get_target_schema()
    if not schema or schema == "public":
        return
    for table in _get_affitti_brevi_tables(schema):
        table.create(bind=bind, checkfirst=True)


def downgrade():
    bind = op.get_bind()
    schema = _get_target_schema()
    if not schema or schema == "public":
        return
    for table in reversed(_get_affitti_brevi_tables(schema)):
        table.drop(bind=bind, checkfirst=True)
