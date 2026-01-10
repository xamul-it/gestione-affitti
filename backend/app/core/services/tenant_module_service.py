"""
Tenant module service for managing per-tenant module installation.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
import logging
from typing import List
from datetime import datetime
from app.core.models.tenant import Tenant, TenantModule


class TenantModuleService:
    """Service for managing tenant-specific module installations."""
    logger = logging.getLogger(__name__)

    # Business module tables (will be created in tenant schemas)
    MODULE_TABLES = {
        "anagrafica_italiana": [
            "soggetti_anagrafici",
            "ruoli_azienda",
            "ruoli_azienda_tipi",
            "ruoli_disponibili",
            "soggetti_ruoli",
            "tipi_documento_overrides",
            "stati_documento_overrides"
        ],
        "immobili": [
            "unita_immobiliari",
            "condomini",
            "proprietari",
            "diritti_immobile",
            "certificati_energetici",
            "tabelle_millesimali",
            "millesimi_unita",
            "documenti",
            "platform_user_dashboards",
            "terreni"
        ],
        "affitti_lungo": [
            "affittuari",
            "contratti",
            "incassi",
            "spese",
            "ripartizioni_spese",
            "tecnici"
        ],
        "affitti_brevi": [
            "prenotazioni",
            "ospiti_prenotazioni",
            "calendari_ical",
            "blocchi_calendario",
            "comunicazioni_polizia",
            "tasse_soggiorno_config",
            "tasse_soggiorno_scaglioni",
            "tasse_prenotazioni",
            "scadenze_affitti_brevi_ext"
        ]
    }

    @staticmethod
    def _config_column_exists(db: Session) -> bool:
        inspector = inspect(db.get_bind())
        columns = inspector.get_columns('tenant_modules', schema='public')
        return any(col['name'] == 'config' for col in columns)

    @staticmethod
    def install_module_for_tenant(tenant_id: int, module_id: str, db: Session):
        """
        Install module tables in tenant schema.

        Args:
            tenant_id: Tenant ID
            module_id: Module ID (e.g., "immobili", "affitti_lungo")
            db: Database session

        Raises:
            ValueError: If tenant not found or module unknown
        """
        # Get tenant
        tenant = db.query(Tenant).get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # Check if module exists
        if module_id not in TenantModuleService.MODULE_TABLES:
            raise ValueError(f"Unknown module: {module_id}")

        # Get module tables
        table_names = TenantModuleService.MODULE_TABLES[module_id]

        # Create tables in tenant schema
        schema_name = tenant.schema_name
        for table_name in table_names:
            try:
                # Copy table structure from public schema
                db.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {schema_name}.{table_name}
                    (LIKE public.{table_name} INCLUDING ALL)
                """))
            except Exception as e:
                print(f"Warning: Could not create {schema_name}.{table_name}: {e}")
                # Continue with other tables

        db.commit()

    @staticmethod
    def sync_module_tables_for_tenant(tenant_id: int, module_id: str, db: Session):
        """
        Ensure tenant tables exist and are aligned with public templates.

        Adds missing columns and indexes when possible.
        """
        tenant = db.query(Tenant).get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        if module_id not in TenantModuleService.MODULE_TABLES:
            raise ValueError(f"Unknown module: {module_id}")

        inspector = inspect(db.get_bind())
        schema_name = tenant.schema_name
        table_names = TenantModuleService.MODULE_TABLES[module_id]

        for table_name in table_names:
            if not inspector.has_table(table_name, schema=schema_name):
                db.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {schema_name}.{table_name}
                    (LIKE public.{table_name} INCLUDING ALL)
                """))
                db.commit()
                continue

            TenantModuleService._sync_table_columns(schema_name, table_name, db)
            TenantModuleService._sync_table_indexes(schema_name, table_name, db)

    @staticmethod
    def _sync_table_columns(schema_name: str, table_name: str, db: Session):
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
                    schema_name,
                    table_name,
                    name,
                    exc,
                )

    @staticmethod
    def _sync_table_indexes(schema_name: str, table_name: str, db: Session):
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
                    idx["indexname"],
                    schema_name,
                    table_name,
                    exc,
                )

        # Register module as enabled
        existing = db.query(TenantModule).filter_by(
            tenant_id=tenant_id,
            module_id=module_id
        ).first()

        if existing:
            # Re-enable if disabled
            existing.enabled = True
            existing.disabled_at = None
        else:
            # Create new registration
            tenant_module = TenantModule(
                tenant_id=tenant_id,
                module_id=module_id,
                enabled=True
            )
            if TenantModuleService._config_column_exists(db):
                tenant_module.config = {}
            db.add(tenant_module)

        db.commit()

    @staticmethod
    def disable_module_for_tenant(tenant_id: int, module_id: str, db: Session):
        """
        Disable module (keep data).

        Args:
            tenant_id: Tenant ID
            module_id: Module ID
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
        # Get tenant
        tenant = db.query(Tenant).get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # Check if module exists
        if module_id not in TenantModuleService.MODULE_TABLES:
            raise ValueError(f"Unknown module: {module_id}")

        if drop_tables:
            # Drop module tables from tenant schema
            schema_name = tenant.schema_name
            table_names = TenantModuleService.MODULE_TABLES[module_id]

            # Drop in reverse order to handle FK dependencies
            for table_name in reversed(table_names):
                try:
                    db.execute(text(f"DROP TABLE IF EXISTS {schema_name}.{table_name} CASCADE"))
                except Exception as e:
                    print(f"Warning: Could not drop {schema_name}.{table_name}: {e}")
                    # Continue with other tables

            db.commit()

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
        # All available modules
        all_module_ids = list(TenantModuleService.MODULE_TABLES.keys())

        tenant_modules = db.query(TenantModule).filter_by(
            tenant_id=tenant_id
        ).all()

        if not tenant_modules:
            from app.core.module_system.models import Module

            enabled_modules = db.query(Module).filter(Module.enabled == True).all()
            has_config = TenantModuleService._config_column_exists(db)
            for module in enabled_modules:
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
        has_config = TenantModuleService._config_column_exists(db)

        return [
            {
                "module_id": module_id,
                "name": module_id.replace('_', ' ').title(),
                "enabled": module_id in enabled_ids,
                "installed_at": module_map[module_id].installed_at.isoformat() if module_id in module_map else None,
                "table_count": len(TenantModuleService.MODULE_TABLES[module_id]),
                "config": module_map[module_id].config if has_config and module_id in module_map else {}
            }
            for module_id in all_module_ids
        ]

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
