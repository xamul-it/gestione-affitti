"""
Create immobili tenant tables.
"""
from alembic import op, context
from sqlalchemy import MetaData, Table, Column, Integer
from app.core.database import Base

import sys
from pathlib import Path

modules_dir = Path(__file__).resolve().parents[2]
if str(modules_dir) not in sys.path:
    sys.path.insert(0, str(modules_dir))

import importlib

for module_name in [
    "immobili.models.tipologia_terreno_override",
    "immobili.models.terreno",
    "immobili.models.unita_immobiliare",
    "immobili.models.condomini",
    "immobili.models.proprietari",
    "immobili.models.diritti_immobile",
    "immobili.models.certificati_energetici",
    "immobili.models.tabelle_millesimali",
    "immobili.models.millesimi_unita",
    "immobili.models.tipo_immobile_categoria_map",
]:
    importlib.import_module(module_name)

# Revision identifiers, used by Alembic.
revision = "2025022002_tenant_tables"
down_revision = "2025022001_public_domain"
branch_labels = None
depends_on = None

target_schema = "tenant"

PUBLIC_TABLES = {
    "immo_categorie_catastali",
    "immo_tipologie_terreno",
}

# Tables created by a LATER, dedicated migration in this same chain, not by
# this one's generic "sweep every immo_-prefixed table off Base.metadata"
# mechanism. Importing any immobili.models.* submodule above runs
# immobili/models/__init__.py in full (Python always executes a package's
# __init__ when importing a submodule), which registers every model on
# Base.metadata regardless of this file's own explicit import list — so
# new immo_ tables added later keep getting swept in here too unless
# excluded. This specific migration's target_metadata only stubs FK targets
# it knew about when written (anag_soggetti_anagrafici, the two public
# terreno/categoria tables) — a table added later with an FK to something
# else (e.g. core_scadenze) would fail to resolve here. Excluding it and
# letting its own migration (with a real database connection, not a stub
# metadata) create it avoids that entirely.
EXCLUDED_TABLES = {
    "immo_conduttori",
    "immo_assegnazioni_conduttore",
    "immo_spese_ricorrenti",
}


def _get_target_schema():
    return context.get_x_argument(as_dictionary=True).get("schema")


def _get_tenant_tables(schema):
    target_metadata = MetaData()
    _ensure_fk_targets(target_metadata, schema)
    for table in Base.metadata.tables.values():
        if (
            table.name.startswith("immo_")
            and table.name not in PUBLIC_TABLES
            and table.name not in EXCLUDED_TABLES
        ):
            table.to_metadata(target_metadata, schema=schema)
    # Avoid sorted_tables to prevent FK resolution against external modules.
    return _order_tenant_tables(list(target_metadata.tables.values()))


def _ensure_fk_targets(target_metadata: MetaData, schema: str) -> None:
    # Add stub tables for FK targets that live outside this module metadata.
    Table(
        "anag_soggetti_anagrafici",
        target_metadata,
        Column("id", Integer, primary_key=True),
        schema=schema,
    )
    Table(
        "immo_categorie_catastali",
        target_metadata,
        Column("id", Integer, primary_key=True),
        schema="public",
    )
    Table(
        "immo_tipologie_terreno",
        target_metadata,
        Column("id", Integer, primary_key=True),
        schema="public",
    )


def _order_tenant_tables(tables: list[Table]) -> list[Table]:
    ordered_names = [
        "immo_condomini",
        "immo_unita_immobiliari",
        "immo_proprietari",
        "immo_diritti_immobile",
        "immo_certificati_energetici",
        "immo_tabelle_millesimali",
        "immo_millesimi_unita",
        "immo_tipologie_terreno_overrides",
        "immo_terreni",
        "immo_tipo_immobile_categoria_map",
    ]
    table_map = {table.name: table for table in tables}
    ordered = [table_map[name] for name in ordered_names if name in table_map]
    ordered.extend([table for table in tables if table.name not in ordered_names])
    return ordered


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
