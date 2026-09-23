"""
Alembic Environment Configuration - Multi-Tenant Support

This env.py supports schema-based multi-tenancy:
- Public schema: domain data (tipi_documento, categorie_catastali, etc.)
- Tenant schemas: business data + overrides (contratti, tipi_documento_overrides, etc.)

Usage:
  alembic upgrade head                    # Migrate public schema (default)
  alembic -x schema=public upgrade head   # Migrate public schema explicitly
  alembic -x schema=all upgrade head      # Migrate ALL schemas (public + all tenants)
  alembic -x schema=tenant_test upgrade head  # Migrate specific tenant

Each migration can specify target_schema in its module:
  target_schema = "public"   # Only runs in public schema
  target_schema = "tenant"   # Only runs in tenant schemas
  target_schema = "both"     # Runs in all schemas (default if not specified)
"""
from logging.config import fileConfig
import sys
from pathlib import Path

from sqlalchemy import engine_from_config, text, inspect
from sqlalchemy import pool

from alembic import context, op as alembic_op

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import Base metadata from app
from app.core.database import Base
from app.core.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url from .env settings
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)

# Optionally override version_locations for module-scoped migrations
module_migrations = context.get_x_argument(as_dictionary=True).get('module_migrations')
if module_migrations:
    config.set_main_option('version_locations', module_migrations)

module_prefix = context.get_x_argument(as_dictionary=True).get('module_prefix')
module_version_table = context.get_x_argument(as_dictionary=True).get('module_version_table')


def _normalize_prefix(prefix: str) -> str:
    if not prefix:
        return ""
    # Lowercased: table-name prefixes are conventionally lowercase
    # throughout this codebase (immo_, anag_, alng_, ...) regardless of how
    # a module's own module_short_code happens to be cased in its manifest
    # (e.g. immobili declares "IMMO"). Comparing/prepending case-sensitively
    # here silently produced tables like "IMMO_immo_conduttori" for any
    # module whose declared code didn't already match this convention's
    # casing — found and fixed while adding immobili's Conduttore/
    # SpesaRicorrenteImmobile migration (which sidesteps the wrapped op.*
    # functions entirely via raw op.execute() SQL, but that's a per-
    # migration workaround, not a fix for this function).
    prefix = prefix.lower()
    return prefix if prefix.endswith("_") else f"{prefix}_"


def _should_prefix(name: str, prefix: str) -> bool:
    if not name or not prefix:
        return False
    if "." in name:
        return False
    return not name.lower().startswith(prefix.lower())


def _apply_prefix(name: str, prefix: str) -> str:
    if _should_prefix(name, prefix):
        return f"{prefix}{name}"
    return name


def _install_module_prefixing(prefix: str) -> None:
    normalized = _normalize_prefix(prefix)
    if not normalized:
        return

    original_create_table = alembic_op.create_table
    original_drop_table = alembic_op.drop_table
    original_add_column = alembic_op.add_column
    original_drop_column = alembic_op.drop_column
    original_alter_column = alembic_op.alter_column
    original_create_index = alembic_op.create_index
    original_drop_index = alembic_op.drop_index
    original_create_foreign_key = alembic_op.create_foreign_key
    original_drop_constraint = alembic_op.drop_constraint
    original_rename_table = getattr(alembic_op, "rename_table", None)

    def create_table(table_name, *args, **kwargs):
        return original_create_table(_apply_prefix(table_name, normalized), *args, **kwargs)

    def drop_table(table_name, *args, **kwargs):
        return original_drop_table(_apply_prefix(table_name, normalized), *args, **kwargs)

    def add_column(table_name, column, *args, **kwargs):
        return original_add_column(_apply_prefix(table_name, normalized), column, *args, **kwargs)

    def drop_column(table_name, column_name, *args, **kwargs):
        return original_drop_column(_apply_prefix(table_name, normalized), column_name, *args, **kwargs)

    def alter_column(table_name, column_name, *args, **kwargs):
        return original_alter_column(_apply_prefix(table_name, normalized), column_name, *args, **kwargs)

    def create_index(index_name, table_name, *args, **kwargs):
        return original_create_index(
            _apply_prefix(index_name, normalized),
            _apply_prefix(table_name, normalized),
            *args,
            **kwargs,
        )

    def drop_index(index_name, *args, **kwargs):
        return original_drop_index(_apply_prefix(index_name, normalized), *args, **kwargs)

    def create_foreign_key(
        constraint_name,
        source_table,
        referent_table,
        local_cols,
        remote_cols,
        *args,
        **kwargs,
    ):
        referent_schema = kwargs.get("referent_schema")
        prefixed_referent = referent_table
        if referent_schema is None:
            prefixed_referent = _apply_prefix(referent_table, normalized)
        return original_create_foreign_key(
            _apply_prefix(constraint_name, normalized) if constraint_name else None,
            _apply_prefix(source_table, normalized),
            prefixed_referent,
            local_cols,
            remote_cols,
            *args,
            **kwargs,
        )

    def drop_constraint(constraint_name, table_name, *args, **kwargs):
        return original_drop_constraint(
            _apply_prefix(constraint_name, normalized) if constraint_name else None,
            _apply_prefix(table_name, normalized),
            *args,
            **kwargs,
        )

    alembic_op.create_table = create_table
    alembic_op.drop_table = drop_table
    alembic_op.add_column = add_column
    alembic_op.drop_column = drop_column
    alembic_op.alter_column = alter_column
    alembic_op.create_index = create_index
    alembic_op.drop_index = drop_index
    alembic_op.create_foreign_key = create_foreign_key
    alembic_op.drop_constraint = drop_constraint

    if original_rename_table:
        def rename_table(old_table_name, new_table_name, *args, **kwargs):
            return original_rename_table(
                _apply_prefix(old_table_name, normalized),
                _apply_prefix(new_table_name, normalized),
                *args,
                **kwargs,
            )

        alembic_op.rename_table = rename_table


if module_prefix:
    _install_module_prefixing(module_prefix)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def get_all_tenant_schemas(connection) -> list:
    """Get all tenant schema names from the database."""
    result = connection.execute(text("""
        SELECT schema_name FROM public.tenants WHERE schema_name IS NOT NULL
    """))
    return [row[0] for row in result.fetchall()]


def get_target_schemas() -> list:
    """
    Determine which schemas to migrate based on -x schema=XXX argument.

    Returns list of schema names to migrate.
    """
    schema_arg = context.get_x_argument(as_dictionary=True).get('schema', 'public')

    if schema_arg == 'public':
        return ['public']
    elif schema_arg == 'all':
        # Will be resolved later when we have a connection
        return ['all']
    else:
        # Specific schema name (e.g., 'tenant_test')
        return [schema_arg]


def should_run_migration_for_schema(schema_name: str) -> bool:
    """
    Check if current migration should run for the given schema.

    Reads target_schema from the migration module:
    - "public": only runs in public schema
    - "tenant": only runs in tenant schemas
    - "both": runs in all schemas (default)
    """
    # Get the current migration's target_schema setting
    migration_context = context.get_context()

    # Try to get target_schema from current migration script
    # Default to "both" if not specified
    script = migration_context.script
    if script and hasattr(script, '_current_rev'):
        current_rev = script._current_rev
        if current_rev:
            rev_script = script.get_revision(current_rev)
            if rev_script and hasattr(rev_script.module, 'target_schema'):
                target = rev_script.module.target_schema

                if target == "public" and schema_name != "public":
                    return False
                elif target == "tenant" and schema_name == "public":
                    return False

    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")

    target_schemas = get_target_schemas()

    # In offline mode, we just generate SQL - use public schema
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_for_schema(connection, schema_name: str) -> None:
    """Run migrations for a specific schema."""
    print(f"\n{'='*60}")
    print(f"Migrating schema: {schema_name}")
    print(f"{'='*60}")

    # Set search_path to the target schema
    connection.execute(text(f"SET search_path TO {schema_name}, public"))
    connection.commit()

    # Configure context for this schema
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table=module_version_table or "alembic_version",
        version_table_schema=schema_name if schema_name != 'public' else None,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()

    print(f"Completed migration for schema: {schema_name}")


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with multi-schema support."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        target_schemas = get_target_schemas()

        # Resolve 'all' to actual tenant schemas
        if target_schemas == ['all']:
            # Get all tenant schemas
            tenant_schemas = get_all_tenant_schemas(connection)
            target_schemas = ['public'] + tenant_schemas
            print(f"Migrating all schemas: {target_schemas}")

        # Run migrations for each target schema
        for schema_name in target_schemas:
            # Verify schema exists
            result = connection.execute(text("""
                SELECT schema_name FROM information_schema.schemata
                WHERE schema_name = :schema
            """), {"schema": schema_name})

            if not result.fetchone():
                print(f"WARNING: Schema '{schema_name}' does not exist, skipping...")
                continue

            run_migrations_for_schema(connection, schema_name)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
