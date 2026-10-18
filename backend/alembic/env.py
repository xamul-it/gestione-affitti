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
import inspect as _inspect
from pathlib import Path

from sqlalchemy import engine_from_config, text, inspect
from sqlalchemy import pool

from alembic import context, op as alembic_op

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import Base metadata from app
from app.core.database import Base
from app.core.config import settings

# Add modules/ directory to path so module migrations can `import <module>.models`
# regardless of whether this runs in-process or as a standalone subprocess.
_modules_dir = str(settings.resolved_module_dir)
if _modules_dir not in sys.path:
    sys.path.insert(0, _modules_dir)

# Eagerly import core platform models so Base.metadata is fully populated
# before any migration runs. A module-scoped migration subprocess only
# imports its own module's models; without this, any cross-module foreign
# key (e.g. a tenant table referencing public.core_document_jobs) fails to
# resolve with NoReferencedTableError even though the target table exists
# in the database, because the referencing model class was never imported
# in this process. Mirrors the "ensure tables are created" imports in
# app/main.py.
from app.core.module_system.models import (  # noqa: F401
    Module, ModuleDependency, ModulePermission, ModuleHook, ModuleExtension, ModuleEndpoint,
)
from app.core.auth.models import User, Role, Permission, user_roles, role_permissions  # noqa: F401
from app.core.models.import_configuration import ImportConfiguration  # noqa: F401
from app.core.models.table_configuration import TableConfiguration  # noqa: F401
from app.core.models import RuoloDisponibile, SoggettoRuolo  # noqa: F401
from app.core.models.tenant import Tenant, UserTenant, TenantModule  # noqa: F401
from app.core.platform.models import (  # noqa: F401
    MenuItem, Widget, UserDashboard, Scadenza, ScadenzaDestinatario, ScadenzaLog, DocumentJob, JobStatus,
    Notifica, CanaleNotifica, StatoEmailNotifica,
)

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
        SELECT schema_name FROM public.core_tenants WHERE schema_name IS NOT NULL
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


def _get_calling_migration_target_schema():
    """
    Walk the call stack to find the migration script module currently
    executing (identified by defining both `revision` and `down_revision`,
    which every Alembic migration file defines) and return its declared
    `target_schema`, or None if not declared / not found.
    """
    for frame_info in _inspect.stack():
        g = frame_info.frame.f_globals
        if 'revision' in g and 'down_revision' in g:
            return g.get('target_schema')
    return None


def should_run_migration_for_schema(schema_name: str) -> bool:
    """
    Check if the currently-executing migration should run against the
    given schema, based on the `target_schema` declared in the migration
    module currently on the call stack:
    - "public": only runs in public schema
    - "tenant": only runs in tenant schemas
    - "both" / not declared: runs in all schemas
    """
    target = _get_calling_migration_target_schema()
    if target == "public" and schema_name != "public":
        return False
    if target == "tenant" and schema_name == "public":
        return False
    return True


def _install_schema_gate() -> None:
    """
    Wrap DDL-emitting op functions so that a migration whose declared
    target_schema doesn't match the schema currently being migrated is
    skipped entirely instead of running against the wrong schema's
    tables (e.g. a tenant-only migration running while migrating public).

    Must be installed after _install_module_prefixing so it wraps
    whatever is currently on `alembic_op` (prefixed or not).
    """
    gated_names = [
        "create_table", "drop_table", "add_column", "drop_column",
        "alter_column", "create_index", "drop_index",
        "create_unique_constraint", "create_check_constraint",
        "create_foreign_key", "drop_constraint", "execute",
        "bulk_insert",
    ]
    if getattr(alembic_op, "rename_table", None):
        gated_names.append("rename_table")

    for name in gated_names:
        original = getattr(alembic_op, name, None)
        if original is None:
            continue

        def make_gated(fn_name, fn):
            def gated(*args, **kwargs):
                schema_name = _current_migration_schema["value"]
                if schema_name is not None and not should_run_migration_for_schema(schema_name):
                    return None
                return fn(*args, **kwargs)
            gated.__name__ = fn_name
            return gated

        setattr(alembic_op, name, make_gated(name, original))


_current_migration_schema = {"value": None}
_install_schema_gate()


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

    _current_migration_schema["value"] = schema_name

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
