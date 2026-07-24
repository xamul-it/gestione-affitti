"""
Tenant module service for managing per-tenant module installation.

This service handles:
- Installing/uninstalling modules for specific tenants
- Running alembic migrations for tenant schemas
- Creating override tables in tenant schemas
- Syncing table structures between public and tenant schemas
"""
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect, MetaData
import logging
import subprocess
import os
import importlib
import sys
import inspect as py_inspect
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from app.core.models.tenant import Tenant, TenantModule
from app.core.module_system.models import Module
from app.core.module_system.alembic_utils import build_module_alembic_config
from app.core.module_system.manifest import parse_manifest, validate_manifest, ManifestValidationError
from app.core.database import Base


class TenantModuleService:
    """Service for managing tenant-specific module installations."""
    logger = logging.getLogger(__name__)

    # Business module tables (created in tenant schemas)
    # Format: module_id -> list of table names
    MODULE_TABLES = {
        "anagrafica_italiana": [
            "anag_soggetti_anagrafici",
            "anag_ruoli_azienda",
            "anag_tipi_documento_overrides",
            "anag_stati_documento_overrides",
            "anag_comuni_italia_overrides",
            "anag_ruoli_azienda_tipi_overrides",
            "anag_documenti",
        ],
        "immobili": [
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
        ],
        "affitti_lungo": [
            "affittuari",
            "contratti",
            "incassi",
            "spese",
            "ripartizioni_spese",
            "tecnici",
        ],
        "affitti_brevi": [
            "ab_canali",
            "ab_calendari_canali",
            "ab_prenotazioni",
            "ab_ospiti_soggiorni",
            "ab_blocchi_calendario",
            "ab_comunicazioni",
            "ab_tasse_soggiorno_config",
            "ab_tasse_soggiorno_scaglioni",
            "ab_tasse_soggiorni",
            "ab_soggiorni",
            "ab_attivita_schedulate",
            "ab_attivita_schedulate_log",
        ]
    }

    # Override tables that reference public domain tables
    # These are created directly in tenant schema (not copied from public)
    OVERRIDE_TABLES = {
        "anag_tipi_documento_overrides": """
            CREATE TABLE IF NOT EXISTS {schema}.anag_tipi_documento_overrides (
                id SERIAL PRIMARY KEY,
                tipo_documento_id INTEGER NOT NULL REFERENCES public.anag_tipi_documento(id) ON DELETE CASCADE,
                codice VARCHAR(50),
                nome VARCHAR(100),
                descrizione VARCHAR(255),
                categoria VARCHAR(50),
                richiede_scadenza BOOLEAN,
                attivo BOOLEAN,
                is_deleted BOOLEAN NOT NULL DEFAULT false,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ,
                UNIQUE(tipo_documento_id)
            )
        """,
        "anag_stati_documento_overrides": """
            CREATE TABLE IF NOT EXISTS {schema}.anag_stati_documento_overrides (
                id SERIAL PRIMARY KEY,
                stato_documento_id INTEGER NOT NULL REFERENCES public.anag_stati_documento(id) ON DELETE CASCADE,
                codice VARCHAR(20),
                nome VARCHAR(100),
                descrizione VARCHAR(255),
                attivo BOOLEAN,
                is_deleted BOOLEAN NOT NULL DEFAULT false,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ,
                UNIQUE(stato_documento_id)
            )
        """,
        "anag_comuni_italia_overrides": """
            CREATE TABLE IF NOT EXISTS {schema}.anag_comuni_italia_overrides (
                id SERIAL PRIMARY KEY,
                comune_id INTEGER NOT NULL REFERENCES public.anag_comuni_italia(id) ON DELETE CASCADE,
                nome VARCHAR(100),
                nome_normalized VARCHAR(100),
                codice_istat VARCHAR(10),
                codice_catastale VARCHAR(10),
                cap VARCHAR(10),
                provincia_sigla VARCHAR(2),
                provincia_nome VARCHAR(100),
                regione VARCHAR(100),
                latitudine NUMERIC(10, 7),
                longitudine NUMERIC(10, 7),
                is_deleted BOOLEAN NOT NULL DEFAULT false,
                deleted_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ,
                UNIQUE(comune_id)
            )
        """,
        "anag_ruoli_azienda_tipi_overrides": """
            CREATE TABLE IF NOT EXISTS {schema}.anag_ruoli_azienda_tipi_overrides (
                id SERIAL PRIMARY KEY,
                ruolo_tipo_id INTEGER NOT NULL REFERENCES public.anag_ruoli_azienda_tipi(id) ON DELETE CASCADE,
                nome VARCHAR(100),
                descrizione VARCHAR(500),
                attivo BOOLEAN,
                is_deleted BOOLEAN NOT NULL DEFAULT false,
                deleted_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ,
                UNIQUE(ruolo_tipo_id)
            )
        """,
        "immo_tipologie_terreno_overrides": """
            CREATE TABLE IF NOT EXISTS {schema}.immo_tipologie_terreno_overrides (
                id SERIAL PRIMARY KEY,
                tipologia_id INTEGER NOT NULL REFERENCES public.immo_tipologie_terreno(id) ON DELETE CASCADE,
                codice VARCHAR(20),
                nome VARCHAR(100),
                descrizione TEXT,
                attivo BOOLEAN,
                is_deleted BOOLEAN NOT NULL DEFAULT false,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ,
                UNIQUE(tipologia_id)
            )
        """,
    }

    @staticmethod
    def _get_tenant_tables(module_id: str, module_record=None) -> List[str]:
        """
        Return the list of tenant schema tables for a module.

        Priority:
        1. manifest['tenant_tables'] (if module_record provided and manifest has it)
        2. MODULE_TABLES legacy fallback
        """
        if module_record is not None:
            manifest = module_record.manifest or {}
            tables = manifest.get("tenant_tables")
            if tables is not None:
                return tables
        return TenantModuleService.MODULE_TABLES.get(module_id, [])

    @staticmethod
    def _get_override_tables_ddl(module_record=None) -> Dict[str, str]:
        """
        Return the override tables DDL dict for a module.

        Priority:
        1. manifest['override_tables_ddl'] (if module_record provided and manifest has it)
        2. OVERRIDE_TABLES legacy fallback (all override tables)
        """
        if module_record is not None:
            manifest = module_record.manifest or {}
            ddl = manifest.get("override_tables_ddl")
            if ddl is not None:
                return ddl
        return TenantModuleService.OVERRIDE_TABLES

    @staticmethod
    def _config_column_exists(db: Session) -> bool:
        """Check if config column exists in tenant_modules table."""
        inspector = inspect(db.get_bind())
        try:
            columns = inspector.get_columns('tenant_modules', schema='public')
            return any(col['name'] == 'config' for col in columns)
        except Exception:
            return False

    @staticmethod
    def run_tenant_migrations(schema_name: str, db: Session) -> bool:
        """
        Run alembic migrations for a specific tenant schema.

        Args:
            schema_name: The tenant schema name
            db: Database session (used to get connection info)

        Returns:
            True if migrations succeeded, False otherwise
        """
        TenantModuleService.logger.info(f"Running migrations for tenant schema: {schema_name}")

        try:
            # Get the backend directory
            backend_dir = Path(__file__).parent.parent.parent.parent

            # Run alembic with schema argument
            result = subprocess.run(
                ["alembic", "-x", f"schema={schema_name}", "upgrade", "head"],
                cwd=str(backend_dir),
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                TenantModuleService.logger.info(f"Migrations completed for {schema_name}")
                TenantModuleService.logger.debug(result.stdout)
                return True
            else:
                TenantModuleService.logger.error(f"Migration failed for {schema_name}: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            TenantModuleService.logger.error(f"Migration timeout for {schema_name}")
            return False

    @staticmethod
    def run_module_tenant_migrations(schema_name: str, module_record: Module) -> bool:
        """
        Run module-scoped migrations for a specific tenant schema.

        Uses module migrations path and module prefix from manifest.
        """
        manifest = module_record.manifest or {}
        migrations_path = manifest.get("migrations_path")
        module_prefix = manifest.get("module_short_code")

        if not migrations_path or not module_prefix:
            TenantModuleService.logger.warning(
                "Module '%s' missing migrations_path or module_short_code for tenant migrations",
                module_record.technical_name,
            )
            return False

        module_dir = Path(module_record.install_path)
        migrations_dir = (module_dir / migrations_path).resolve()
        if not migrations_dir.exists():
            TenantModuleService.logger.warning(
                "Module '%s' migrations_path not found: %s",
                module_record.technical_name,
                migrations_dir,
            )
            return False

        TenantModuleService.logger.info(
            "Running module migrations for '%s' on tenant schema '%s'",
            module_record.technical_name,
            schema_name,
        )

        try:
            backend_dir = Path(__file__).parent.parent.parent.parent
            config_path = build_module_alembic_config(backend_dir, migrations_dir)
            try:
                result = subprocess.run(
                    [
                        "alembic",
                        "-c",
                        str(config_path),
                        "-x",
                        f"schema={schema_name}",
                        "-x",
                        f"module_prefix={module_prefix}",
                        "-x",
                        f"module_version_table=alembic_version_{module_prefix}",
                        "upgrade",
                        "head",
                    ],
                    cwd=str(backend_dir),
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
            finally:
                config_path.unlink(missing_ok=True)

            if result.returncode == 0:
                TenantModuleService.logger.info(
                    "Module migrations completed for '%s' on %s",
                    module_record.technical_name,
                    schema_name,
                )
                TenantModuleService.logger.debug(result.stdout)
                return True

            TenantModuleService.logger.error(
                "Module migration failed for '%s' on %s: %s",
                module_record.technical_name,
                schema_name,
                result.stderr.strip() or result.stdout.strip(),
            )
            return False

        except subprocess.TimeoutExpired:
            TenantModuleService.logger.error(
                "Module migration timeout for '%s' on %s",
                module_record.technical_name,
                schema_name,
            )
            return False
        except Exception as e:
            TenantModuleService.logger.error(f"Migration error for {schema_name}: {e}")
            return False

    @staticmethod
    def create_override_tables(schema_name: str, db: Session, module_record=None) -> Dict[str, bool]:
        """
        Create override tables in a tenant schema for a given module.

        Override tables store tenant-specific customizations of domain data.
        DDL is read from manifest['override_tables_ddl'] when available,
        falling back to the legacy OVERRIDE_TABLES dict.

        Args:
            schema_name: The tenant schema name
            db: Database session
            module_record: Optional Module record; if provided, reads DDL from manifest

        Returns:
            Dict mapping table name to success status
        """
        results = {}
        override_ddl = TenantModuleService._get_override_tables_ddl(module_record)

        for table_name, ddl_template in override_ddl.items():
            try:
                ddl = ddl_template.format(schema=schema_name)
                db.execute(text(ddl))
                db.commit()
                results[table_name] = True
                TenantModuleService.logger.info(f"Created override table: {schema_name}.{table_name}")
            except Exception as e:
                db.rollback()
                results[table_name] = False
                TenantModuleService.logger.warning(f"Failed to create {schema_name}.{table_name}: {e}")

        return results

    @staticmethod
    def _create_module_tables_from_metadata(
        module_id: str,
        module_record: Module,
        schema_name: str,
        db: Session
    ) -> List[str]:
        """
        Fallback table creation using SQLAlchemy metadata.

        Returns a list of tables created.
        """
        try:
            TenantModuleService._import_module_from_path(module_record)
        except Exception as exc:
            TenantModuleService.logger.warning(
                "Failed importing module '%s' for metadata: %s",
                module_id,
                exc,
            )
        table_names = TenantModuleService._get_tenant_tables(module_id, module_record)
        if not table_names:
            return []

        target_metadata = MetaData()
        copied: Dict[tuple, object] = {}

        def _copy_table(lookup_key: str, table_name: str, target_schema: str):
            """
            Copy a table into target_metadata under target_schema, recursively
            copying any FK-referenced tables first under THEIR OWN original
            schema (e.g. public domain tables referenced by a tenant table
            must stay in 'public', not be remapped to the tenant schema).
            """
            cache_key = (target_schema, table_name)
            if cache_key in copied:
                return copied[cache_key]
            source_table = Base.metadata.tables.get(lookup_key)
            if source_table is None:
                return None
            for fk in source_table.foreign_keys:
                ref_table = fk.column.table
                if ref_table.key == lookup_key:
                    continue
                _copy_table(ref_table.key, ref_table.name, ref_table.schema or target_schema)
            copied_table = source_table.to_metadata(target_metadata, schema=target_schema)
            copied[cache_key] = copied_table
            return copied_table

        for table_name in table_names:
            _copy_table(table_name, table_name, schema_name)

        created = []
        bind = db.get_bind()
        for table_name in table_names:
            table = target_metadata.tables.get(f"{schema_name}.{table_name}")
            if table is None:
                continue
            table.create(bind=bind, checkfirst=True)
            created.append(table_name)

        return created

    @staticmethod
    def install_module_for_tenant(
        tenant_id: int,
        module_id: str,
        db: Session,
        run_migrations: bool = True,
        seed_test_data: bool = False,
    ) -> Dict[str, any]:
        """
        Install module tables in tenant schema.

        This method:
        1. Verifies tenant exists
        2. Creates override tables (tenant-specific)
        3. Copies business tables from public template
        4. Optionally runs alembic migrations
        5. Registers module as installed

        Args:
            tenant_id: Tenant ID
            module_id: Module ID (e.g., "immobili", "affitti_lungo")
            db: Database session
            run_migrations: Whether to run alembic migrations

        Returns:
            Dict with installation results

        Raises:
            ValueError: If tenant not found or module unknown
        """
        # Get tenant
        tenant = db.query(Tenant).get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        module_record = db.query(Module).filter(Module.technical_name == module_id).first()
        if not module_record:
            raise ValueError(f"Module '{module_id}' is not registered in the platform")
        if not module_record.registered:
            raise ValueError(f"Module '{module_id}' is not registered in the platform")

        manifest_path = Path(module_record.install_path) / "__manifest__.py"
        if manifest_path.exists():
            try:
                manifest = parse_manifest(manifest_path)
                validate_manifest(manifest)
                module_record.manifest = manifest
                module_record.name = manifest.get("name", module_record.name)
                module_record.version = manifest.get("version", module_record.version)
                module_record.author = manifest.get("author", module_record.author)
                module_record.category = None
                module_record.icon = manifest.get("icon", module_record.icon)
                db.commit()
            except ManifestValidationError as exc:
                TenantModuleService.logger.warning(
                    "Manifest validation failed for %s: %s",
                    module_record.technical_name,
                    exc,
                )
            except Exception as exc:
                TenantModuleService.logger.warning(
                    "Manifest refresh failed for %s: %s",
                    module_record.technical_name,
                    exc,
                )

        schema_name = tenant.schema_name
        table_names = TenantModuleService._get_tenant_tables(module_id, module_record)
        results = {
            "tenant_id": tenant_id,
            "module_id": module_id,
            "schema": schema_name,
            "tables_created": [],
            "tables_failed": [],
            "migrations_run": False,
        }

        TenantModuleService.logger.info(f"Installing module {module_id} for tenant {schema_name}")

        # 1. Check dependencies (must be enabled in tenant)
        dependencies = manifest.get("dependencies", []) if isinstance(manifest.get("dependencies"), list) else []
        missing_deps = []
        for dep in dependencies:
            dep_enabled = db.query(TenantModule).filter_by(
                tenant_id=tenant_id,
                module_id=dep,
                enabled=True,
            ).first()
            if not dep_enabled:
                missing_deps.append(dep)
        if missing_deps:
            raise ValueError(
                f"Missing dependencies for '{module_id}': {', '.join(missing_deps)}. "
                "Enable them first for this tenant."
            )

        # 2. Run module-scoped migrations for tenant schema
        if run_migrations:
            results["migrations_run"] = TenantModuleService.run_module_tenant_migrations(
                schema_name,
                module_record,
            )
            if not results["migrations_run"]:
                raise ValueError(f"Tenant migrations failed for '{module_id}'. Check server logs.")

        # 3. Run module install endpoint (tenant scope)
        if not TenantModuleService._run_module_install(
            module_record,
            tenant_id,
            schema_name,
            db,
            seed_test_data=seed_test_data,
        ):
            raise ValueError(f"Module install endpoint failed for '{module_id}'")

        # 3b. Verify tenant tables exist after install
        inspector = inspect(db.get_bind())
        schema_tables = set(inspector.get_table_names(schema=schema_name))
        expected_tables = TenantModuleService._get_tenant_tables(module_id, module_record)
        missing_tables = [table for table in expected_tables if table not in schema_tables]
        if missing_tables:
            try:
                TenantModuleService.logger.warning(
                    "Missing tenant tables for '%s'. Attempting fallback create: %s",
                    module_id,
                    ", ".join(missing_tables),
                )
                TenantModuleService._create_module_tables_from_metadata(
                    module_id,
                    module_record,
                    schema_name,
                    db,
                )
                inspector = inspect(db.get_bind())
                schema_tables = set(inspector.get_table_names(schema=schema_name))
                missing_tables = [table for table in expected_tables if table not in schema_tables]
            except Exception as exc:
                TenantModuleService.logger.warning(
                    "Fallback table creation failed for '%s': %s",
                    module_id,
                    exc,
                )
            if missing_tables:
                raise ValueError(
                    f"Tenant tables missing for '{module_id}': {', '.join(missing_tables)}"
                )

        # 4. Register module as installed
        TenantModuleService._register_module(tenant_id, module_id, db, version=module_record.version)

        return results

    @staticmethod
    def _import_module_from_path(module_record: Module):
        module_path = Path(module_record.install_path)
        module_parent = str(module_path.parent)
        if module_parent not in sys.path:
            sys.path.insert(0, module_parent)
        try:
            return importlib.import_module(module_path.name)
        finally:
            if module_parent in sys.path:
                sys.path.remove(module_parent)

    @staticmethod
    def _call_install_entry(
        module_name: str,
        entry_point: str,
        db: Session,
        tenant_id: int,
        tenant_schema: str,
        seed_test_data: bool,
    ) -> None:
        if ':' in entry_point:
            module_path, function_name = entry_point.split(':', 1)
        else:
            module_path = entry_point
            function_name = 'install'

        current = importlib.import_module(module_name)
        if module_path == function_name and hasattr(current, function_name):
            module_path = ""
        if module_path:
            try:
                current = importlib.import_module(f"{module_name}.{module_path}")
            except Exception:
                parts = module_path.split('.')
                for part in parts:
                    if not hasattr(current, part):
                        raise AttributeError(f"Install entry point '{entry_point}' not found in module")
                    current = getattr(current, part)

        if callable(current) and getattr(current, "__name__", None) == function_name:
            func = current
        else:
            if not hasattr(current, function_name):
                raise AttributeError(f"Install entry point function '{function_name}' not found in '{module_path}'")
            func = getattr(current, function_name)
        if not callable(func):
            raise TypeError(f"Install entry point '{entry_point}' is not callable")

        try:
            signature = py_inspect.signature(func)
        except (TypeError, ValueError):
            func(db, tenant_id, tenant_schema)
            return

        params = list(signature.parameters.values())
        if not params:
            func()
            return

        allowed = {"db", "session", "tenant_id", "tenant_schema", "seed_test_data"}
        has_var_kw = any(p.kind == py_inspect.Parameter.VAR_KEYWORD for p in params)
        has_var_pos = any(p.kind == py_inspect.Parameter.VAR_POSITIONAL for p in params)
        all_named = all(
            p.kind in (py_inspect.Parameter.POSITIONAL_OR_KEYWORD, py_inspect.Parameter.KEYWORD_ONLY)
            and p.name in allowed
            for p in params
        )

        if all_named or has_var_kw:
            kwargs = {}
            if "db" in signature.parameters:
                kwargs["db"] = db
            if "session" in signature.parameters:
                kwargs["session"] = db
            if "tenant_id" in signature.parameters:
                kwargs["tenant_id"] = tenant_id
            if "tenant_schema" in signature.parameters:
                kwargs["tenant_schema"] = tenant_schema
            if "seed_test_data" in signature.parameters:
                kwargs["seed_test_data"] = seed_test_data
            func(**kwargs)
            return

        # Fallback to positional calling convention
        count = len(params)
        if count == 1:
            func(db)
        elif count == 2:
            func(db, tenant_id)
        elif count == 3:
            func(db, tenant_id, tenant_schema)
        else:
            func(db, tenant_id, tenant_schema, seed_test_data)

    @staticmethod
    def _run_module_install(
        module_record: Module,
        tenant_id: int,
        tenant_schema: str,
        db: Session,
        seed_test_data: bool,
    ) -> bool:
        manifest = module_record.manifest or {}
        schema_target = manifest.get("schema_target")
        if schema_target not in {"tenant", "public + tenant"}:
            return True

        endpoints = manifest.get("endpoints", {}) if isinstance(manifest.get("endpoints"), dict) else {}
        install_endpoint = endpoints.get("install")
        if not install_endpoint:
            TenantModuleService.logger.info(
                "Module '%s' has no install endpoint; skipping install step",
                module_record.technical_name,
            )
            return True

        seeds_path = manifest.get("seeds_path")
        if seeds_path:
            seeds_dir = (Path(module_record.install_path) / seeds_path).resolve()
            if not seeds_dir.exists():
                TenantModuleService.logger.warning(
                    "Module '%s' seeds_path not found: %s",
                    module_record.technical_name,
                    seeds_dir,
                )

        try:
            db.connection().execute(text(f"SET search_path TO {tenant_schema}, public"))
            TenantModuleService._call_install_entry(
                module_record.technical_name,
                install_endpoint,
                db,
                tenant_id,
                tenant_schema,
                seed_test_data,
            )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            TenantModuleService.logger.warning(
                "Tenant install failed for module '%s': %s",
                module_record.technical_name,
                e,
            )
            return False

    @staticmethod
    def _register_module(tenant_id: int, module_id: str, db: Session, version: Optional[str] = None) -> TenantModule:
        """Register or re-enable a module for a tenant."""
        existing = db.query(TenantModule).filter_by(
            tenant_id=tenant_id,
            module_id=module_id
        ).first()

        if existing:
            existing.enabled = True
            existing.disabled_at = None
        else:
            tenant_module = TenantModule(
                tenant_id=tenant_id,
                module_id=module_id,
                enabled=True
            )
            if TenantModuleService._config_column_exists(db):
                tenant_module.config = {}
            db.add(tenant_module)
            existing = tenant_module

        if version is not None:
            existing.installed_version = version

        db.commit()
        return existing

    @staticmethod
    def sync_module_tables_for_tenant(tenant_id: int, module_id: str, db: Session):
        """
        Ensure tenant tables exist and are aligned with public templates.

        Adds missing columns and indexes when possible.
        """
        tenant = db.query(Tenant).get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        module_record = db.query(Module).filter(Module.technical_name == module_id).first()
        if not module_record:
            raise ValueError(f"Unknown module: {module_id}")

        schema_name = tenant.schema_name
        table_names = TenantModuleService._get_tenant_tables(module_id, module_record)
        override_ddl = TenantModuleService._get_override_tables_ddl(module_record)

        # First, ensure override tables exist
        TenantModuleService.create_override_tables(schema_name, db, module_record)

        inspector = inspect(db.get_bind())

        for table_name in table_names:
            # Skip override tables (handled above)
            if table_name in override_ddl:
                continue

            if not inspector.has_table(table_name, schema=schema_name):
                # Check if template exists
                if inspector.has_table(table_name, schema='public'):
                    db.execute(text(f"""
                        CREATE TABLE IF NOT EXISTS {schema_name}.{table_name}
                        (LIKE public.{table_name} INCLUDING ALL)
                    """))
                    db.commit()
                continue

            TenantModuleService._sync_table_columns(schema_name, table_name, db)
            TenantModuleService._sync_table_indexes(schema_name, table_name, db)

        # Register module (bumps installed_version to the module's current version)
        TenantModuleService._register_module(tenant_id, module_id, db, version=module_record.version)

    @staticmethod
    def reseed_test_data_for_tenant(tenant_id: int, module_id: str, db: Session) -> bool:
        """
        Re-run a module's install entry point with seed_test_data=True for a
        tenant where the module is already installed. Does not touch table
        structure — only re-invokes whatever seeding logic the module's
        install() function runs when seed_test_data is True.
        """
        tenant = db.query(Tenant).get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        module_record = db.query(Module).filter(Module.technical_name == module_id).first()
        if not module_record:
            raise ValueError(f"Unknown module: {module_id}")

        return TenantModuleService._run_module_install(
            module_record,
            tenant_id,
            tenant.schema_name,
            db,
            seed_test_data=True,
        )

    @staticmethod
    def _sync_table_columns(schema_name: str, table_name: str, db: Session):
        """Sync missing columns from public template to tenant table."""
        public_cols = db.execute(text("""
            SELECT
                a.attname AS column_name,
                format_type(a.atttypid, a.atttypmod) AS data_type,
                pg_get_expr(ad.adbin, ad.adrelid) AS default_value,
                a.attnotnull AS notnull
            FROM pg_attribute a
            JOIN pg_class c ON a.attrelid = c.oid
            JOIN pg_namespace n ON c.relnamespace = n.oid
            LEFT JOIN pg_attrdef ad ON ad.adrelid = a.attrelid AND ad.adnum = a.attnum
            WHERE n.nspname = 'public'
              AND c.relname = :table
              AND a.attnum > 0
              AND NOT a.attisdropped
        """), {"table": table_name}).mappings().all()

        tenant_cols = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = :table
        """), {"schema": schema_name, "table": table_name}).mappings().all()

        tenant_col_names = {row["column_name"] for row in tenant_cols}

        for col in public_cols:
            name = col["column_name"]
            if name in tenant_col_names:
                continue

            ddl = f"ALTER TABLE {schema_name}.{table_name} ADD COLUMN {name} {col['data_type']}"
            default_value = col["default_value"]
            if default_value:
                ddl += f" DEFAULT {default_value}"
            if col["notnull"] and default_value:
                ddl += " NOT NULL"

            try:
                db.execute(text(ddl))
                db.commit()
                TenantModuleService.logger.info(
                    "Added column %s.%s.%s", schema_name, table_name, name
                )
            except Exception as exc:
                db.rollback()
                TenantModuleService.logger.warning(
                    "Failed adding column %s.%s.%s: %s",
                    schema_name, table_name, name, exc,
                )

    @staticmethod
    def _sync_table_indexes(schema_name: str, table_name: str, db: Session):
        """Sync missing indexes from public template to tenant table."""
        public_indexes = db.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename = :table
        """), {"table": table_name}).mappings().all()

        tenant_indexes = db.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = :schema
              AND tablename = :table
        """), {"schema": schema_name, "table": table_name}).mappings().all()

        tenant_index_names = {row["indexname"] for row in tenant_indexes}

        for idx in public_indexes:
            if idx["indexname"] in tenant_index_names:
                continue

            indexdef = idx["indexdef"].replace("CREATE INDEX ", "CREATE INDEX IF NOT EXISTS ")
            indexdef = indexdef.replace("ON public.", f"ON {schema_name}.")

            try:
                db.execute(text(indexdef))
                db.commit()
                TenantModuleService.logger.info(
                    "Added index %s on %s.%s", idx["indexname"], schema_name, table_name
                )
            except Exception as exc:
                db.rollback()
                TenantModuleService.logger.warning(
                    "Failed adding index %s on %s.%s: %s",
                    idx["indexname"], schema_name, table_name, exc,
                )

    @staticmethod
    def disable_module_for_tenant(tenant_id: int, module_id: str, db: Session, drop_tables: bool = False):
        """
        Disable module (keep data).

        Args:
            tenant_id: Tenant ID
            module_id: Module ID
            drop_tables: Whether to drop tenant tables for the module
            db: Database session
        """
        tenant_module = db.query(TenantModule).filter_by(
            tenant_id=tenant_id,
            module_id=module_id
        ).first()

        if tenant_module:
            tenant_module.enabled = False
            tenant_module.disabled_at = datetime.utcnow()
            db.commit()

        if drop_tables:
            return TenantModuleService.drop_module_tables_for_tenant(tenant_id, module_id, db)
        return {"dropped": [], "failed": []}

    @staticmethod
    def drop_module_tables_for_tenant(tenant_id: int, module_id: str, db: Session) -> Dict[str, List[Dict]]:
        """
        Drop tenant schema tables for a module.

        Returns a list of dropped tables.
        """
        tenant = db.query(Tenant).get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        module_record = db.query(Module).filter(Module.technical_name == module_id).first()
        if not module_record:
            raise ValueError(f"Module '{module_id}' is not registered in the platform")

        schema_name = tenant.schema_name
        inspector = inspect(db.get_bind())
        schema_tables = set(inspector.get_table_names(schema=schema_name))
        tenant_tables = TenantModuleService._get_tenant_tables_for_module(
            module_id,
            module_record,
            schema_tables,
        )

        dropped: List[str] = []
        failed: List[Dict[str, str]] = []
        for table in sorted(tenant_tables):
            try:
                db.execute(text("SET LOCAL lock_timeout = '2s'"))
                db.execute(text("SET LOCAL statement_timeout = '10s'"))
                # Avoid deadlocks by taking an exclusive lock without waiting.
                db.execute(
                    text(
                        f'LOCK TABLE "{schema_name}"."{table}" IN ACCESS EXCLUSIVE MODE NOWAIT'
                    )
                )
                db.execute(text(f'DROP TABLE IF EXISTS "{schema_name}"."{table}" CASCADE'))
                db.commit()
                dropped.append(table)
            except Exception as exc:
                db.rollback()
                TenantModuleService.logger.warning(
                    "Failed dropping table %s.%s: %s",
                    schema_name,
                    table,
                    exc,
                )
                failed.append({"table": table, "error": str(exc)})

        manifest = module_record.manifest or {}
        module_prefix = manifest.get("module_short_code")
        if module_prefix:
            version_table = f"alembic_version_{module_prefix}"
            try:
                db.execute(text(f'DROP TABLE IF EXISTS "{schema_name}"."{version_table}"'))
                db.commit()
                dropped.append(version_table)
            except Exception as exc:
                db.rollback()
                TenantModuleService.logger.warning(
                    "Failed dropping alembic version table %s.%s: %s",
                    schema_name,
                    version_table,
                    exc,
                )
                failed.append({"table": version_table, "error": str(exc)})

        return {"dropped": [{"table": name} for name in dropped], "failed": failed}

    @staticmethod
    def uninstall_module_for_tenant(
        tenant_id: int,
        module_id: str,
        drop_tables: bool,
        db: Session
    ):
        """
        Uninstall module and optionally drop tables.

        Args:
            tenant_id: Tenant ID
            module_id: Module ID
            drop_tables: Whether to drop module tables
            db: Database session

        Raises:
            ValueError: If tenant not found or module unknown
        """
        tenant = db.query(Tenant).get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        module_record = db.query(Module).filter(Module.technical_name == module_id).first()
        if not module_record:
            raise ValueError(f"Unknown module: {module_id}")

        if drop_tables:
            schema_name = tenant.schema_name
            table_names = TenantModuleService._get_tenant_tables(module_id, module_record)

            # Drop in reverse order to handle FK dependencies
            for table_name in reversed(table_names):
                try:
                    db.execute(text("SET LOCAL lock_timeout = '5s'"))
                    db.execute(text("SET LOCAL statement_timeout = '30s'"))
                    db.execute(text(f'DROP TABLE IF EXISTS "{schema_name}"."{table_name}" CASCADE'))
                except Exception as e:
                    db.rollback()
                    TenantModuleService.logger.warning(
                        f"Could not drop {schema_name}.{table_name}: {e}"
                    )
                else:
                    db.commit()

            # Ensure we have a clean transaction state
            try:
                db.commit()
            except Exception:
                db.rollback()

        # Remove registration
        db.query(TenantModule).filter_by(
            tenant_id=tenant_id,
            module_id=module_id
        ).delete()

        db.commit()

    @staticmethod
    def get_tenant_modules(tenant_id: int, db: Session) -> List[dict]:
        """
        Get all modules and their status for a tenant.

        Args:
            tenant_id: Tenant ID
            db: Database session

        Returns:
            List of module dicts with status
        """
        from app.core.module_system.models import Module

        tenant = db.query(Tenant).get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        installed_modules = db.query(Module).filter(
            Module.registered == True,
        ).all()
        installed_modules = [
            module
            for module in installed_modules
            if module.state != "broken" or (module.manifest or {}).get("schema_target") == "tenant"
        ]
        module_records = {m.technical_name: m for m in installed_modules}
        all_module_ids = [m.technical_name for m in installed_modules]

        tenant_modules = db.query(TenantModule).filter_by(
            tenant_id=tenant_id
        ).all()
        tenant_module_ids = {tm.module_id for tm in tenant_modules}

        if tenant_module_ids:
            extra_modules = db.query(Module).filter(
                Module.technical_name.in_(tenant_module_ids)
            ).all()
            for module in extra_modules:
                module_records.setdefault(module.technical_name, module)
            all_module_ids = sorted(set(all_module_ids).union(tenant_module_ids))

        if not tenant_modules:
            registered_modules = db.query(Module).filter(Module.registered == True).all()
            has_config = TenantModuleService._config_column_exists(db)
            for module in registered_modules:
                tenant_module = TenantModule(
                    tenant_id=tenant_id,
                    module_id=module.technical_name,
                    enabled=True
                )
                if has_config:
                    tenant_module.config = {}
                db.add(tenant_module)
            db.commit()
            tenant_modules = db.query(TenantModule).filter_by(
                tenant_id=tenant_id
            ).all()

        enabled_ids = {tm.module_id for tm in tenant_modules if tm.enabled}
        module_map = {tm.module_id: tm for tm in tenant_modules}
        tenant_schema = tenant.schema_name
        inspector = inspect(db.get_bind())
        schema_tables = set(inspector.get_table_names(schema=tenant_schema))
        has_config = TenantModuleService._config_column_exists(db)

        modules_payload = []
        for module_id in all_module_ids:
            module_record = module_records.get(module_id)
            tenant_tables = TenantModuleService._get_tenant_tables_for_module(
                module_id,
                module_record,
                schema_tables,
            )
            manifest = module_record.manifest if module_record else {}
            schema_target = (manifest or {}).get("schema_target")
            requires_tenant_tables = schema_target in {"tenant", "public + tenant"}
            effective_enabled = module_id in enabled_ids
            needs_install = False
            if requires_tenant_tables and effective_enabled and len(tenant_tables) == 0:
                needs_install = True
                effective_enabled = False

            installed_version = module_map[module_id].installed_version if module_id in module_map else None
            current_version = module_record.version if module_record else None
            needs_update = bool(
                installed_version is not None
                and current_version is not None
                and installed_version != current_version
            )

            modules_payload.append({
                "module_id": module_id,
                "name": (module_record.name if module_record else module_id.replace('_', ' ').title()),
                "version": current_version,
                "description": (module_record.description or (manifest or {}).get("description", "")) if module_record else "",
                "author": (manifest or {}).get("author") if module_record else None,
                "icon": (module_record.icon or (manifest or {}).get("icon")) if module_record else None,
                "category": (module_record.category or (manifest or {}).get("category") or "other") if module_record else "other",
                "dependencies": (manifest or {}).get("dependencies", []) if module_record else [],
                "enabled": effective_enabled,
                "needs_install": needs_install,
                "installed_at": module_map[module_id].installed_at.isoformat() if module_id in module_map else None,
                "installed_version": installed_version,
                "needs_update": needs_update,
                "tenant_tables": tenant_tables,
                "table_count": len(tenant_tables),
                "config": module_map[module_id].config if has_config and module_id in module_map else {}
            })

        return modules_payload

    @staticmethod
    def _get_tenant_tables_for_module(module_id: str, module_record: Optional[Module], schema_tables: set) -> List[str]:
        # 1. Try manifest tenant_tables first
        expected_tables = TenantModuleService._get_tenant_tables(module_id, module_record)
        if expected_tables:
            return [table for table in expected_tables if table in schema_tables]

        # 2. Fallback: discover by module prefix
        if module_record:
            manifest = module_record.manifest or {}
            prefix = manifest.get("table_prefix") or manifest.get("module_short_code") or ""
            prefix = prefix.lower()
            if prefix and not prefix.endswith("_"):
                prefix = f"{prefix}_"
            if prefix:
                prefixed_tables = sorted([table for table in schema_tables if table.startswith(prefix)])
                if prefixed_tables:
                    return prefixed_tables

        return []

    @staticmethod
    def update_module_config(
        tenant_id: int,
        module_id: str,
        config: dict,
        db: Session
    ) -> TenantModule:
        """
        Update tenant-specific configuration for a module.

        Creates a tenant module record if missing.
        """
        if not TenantModuleService._config_column_exists(db):
            raise ValueError("Tenant module config column missing. Run migrations to enable config.")

        tenant_module = db.query(TenantModule).filter_by(
            tenant_id=tenant_id,
            module_id=module_id
        ).first()

        if not tenant_module:
            tenant_module = TenantModule(
                tenant_id=tenant_id,
                module_id=module_id,
                enabled=True
            )
            tenant_module.config = {}
            db.add(tenant_module)

        tenant_module.config = config or {}
        db.commit()
        db.refresh(tenant_module)
        return tenant_module

    @staticmethod
    def initialize_all_tenants(db: Session) -> Dict[str, Dict]:
        """
        Initialize all existing tenants with override tables.

        Called on application startup to ensure all tenants have
        the correct table structure.

        Returns:
            Dict mapping tenant schema to initialization results
        """
        results = {}

        tenants = db.query(Tenant).filter(Tenant.schema_name.isnot(None)).all()

        for tenant in tenants:
            try:
                override_results = TenantModuleService.create_override_tables(
                    tenant.schema_name, db
                )
                results[tenant.schema_name] = {
                    "success": True,
                    "tables": override_results
                }
            except Exception as e:
                results[tenant.schema_name] = {
                    "success": False,
                    "error": str(e)
                }

        return results
