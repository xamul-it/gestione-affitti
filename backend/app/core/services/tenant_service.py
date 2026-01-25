"""
Tenant service for managing multi-tenant operations.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict
from app.core.models.tenant import Tenant, UserTenant, TenantModule
import subprocess
import tempfile
import os
from datetime import datetime


class TenantService:
    """Service for managing multi-tenant operations."""

    @staticmethod
    def set_tenant_context(schema_name: str, db: Session):
        """
        Set PostgreSQL search_path to tenant schema.

        Args:
            schema_name: The tenant schema name (e.g., "tenant_test")
            db: Database session

        Raises:
            ValueError: If schema name is invalid
        """
        # Validate schema name (security)
        if not schema_name.replace('_', '').replace('-', '').isalnum():
            raise ValueError(f"Invalid schema name: {schema_name}")

        # Set search_path: check tenant schema first, then public for shared data
        db.execute(text(f"SET search_path TO {schema_name}, public"))
        db.commit()

    @staticmethod
    def create_tenant_schema(tenant: Tenant, db: Session):
        """
        Create PostgreSQL schema for new tenant.

        Args:
            tenant: Tenant object with schema_name
            db: Database session

        Raises:
            Exception: If schema creation fails
        """
        schema_name = tenant.schema_name

        # Validate schema name
        if not schema_name.replace('_', '').replace('-', '').isalnum():
            raise ValueError(f"Invalid schema name: {schema_name}")

        # Create schema
        db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))

        # Grant permissions to application user
        db.execute(text(f"GRANT ALL ON SCHEMA {schema_name} TO affitti"))

        db.commit()

    @staticmethod
    def drop_tenant_schema(schema_name: str, db: Session, cascade: bool = False):
        """
        Drop PostgreSQL schema for tenant.

        Args:
            schema_name: The tenant schema name
            db: Database session
            cascade: Whether to drop all objects in schema

        Raises:
            ValueError: If trying to drop public schema
        """
        # Safety check
        if schema_name.lower() in ['public', 'pg_catalog', 'information_schema']:
            raise ValueError(f"Cannot drop system schema: {schema_name}")

        # Validate schema name
        if not schema_name.replace('_', '').replace('-', '').isalnum():
            raise ValueError(f"Invalid schema name: {schema_name}")

        cascade_sql = "CASCADE" if cascade else "RESTRICT"
        db.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} {cascade_sql}"))
        db.commit()

    @staticmethod
    def clear_tenant_tables(schema_name: str, db: Session, force: bool = False) -> Dict[str, List[Dict]]:
        """
        Drop all tables in a tenant schema, preserving the schema itself.

        Args:
            schema_name: The tenant schema name
            db: Database session

        Returns:
            List of dropped table names
        """
        # Safety check
        if schema_name.lower() in ['public', 'pg_catalog', 'information_schema']:
            raise ValueError(f"Cannot clear system schema: {schema_name}")

        # Validate schema name
        if not schema_name.replace('_', '').replace('-', '').isalnum():
            raise ValueError(f"Invalid schema name: {schema_name}")

        if force:
            # Terminate only sessions that hold locks in the target schema.
            TenantService.terminate_schema_connections(db, schema_name=schema_name)

        # Use longer timeouts when forcing cleanup to reduce lock-timeout failures.
        lock_timeout = "20s" if force else "5s"
        statement_timeout = "120s" if force else "30s"

        tables = db.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :schema
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """), {"schema": schema_name}).mappings().all()

        dropped = []
        failed = []
        for row in tables:
            table_name = row["table_name"]
            attempts = 3 if force else 1
            for attempt in range(1, attempts + 1):
                try:
                    db.execute(text(f"SET LOCAL lock_timeout = '{lock_timeout}'"))
                    db.execute(text(f"SET LOCAL statement_timeout = '{statement_timeout}'"))
                    db.execute(text(f'DROP TABLE IF EXISTS "{schema_name}"."{table_name}" CASCADE'))
                    db.commit()
                    dropped.append(table_name)
                    break
                except Exception as exc:
                    db.rollback()
                    if attempt >= attempts:
                        failed.append({
                            "table": table_name,
                            "error": str(exc),
                        })
                    else:
                        continue

        return {"dropped": dropped, "failed": failed}

    @staticmethod
    def clear_non_core_tables(db: Session, schema_name: str = "public", force: bool = False) -> List[str]:
        """
        Drop all non-core tables in a schema.

        Core tables are identified by the "core_" prefix. Alembic version
        tables are preserved.
        """
        if schema_name.lower() in ['pg_catalog', 'information_schema']:
            raise ValueError(f"Cannot clear system schema: {schema_name}")

        if not schema_name.replace('_', '').replace('-', '').isalnum():
            raise ValueError(f"Invalid schema name: {schema_name}")

        if force:
            TenantService.terminate_db_connections(db)

        db.execute(text("SET LOCAL lock_timeout = '5s'"))
        db.execute(text("SET LOCAL statement_timeout = '30s'"))

        tables = db.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :schema
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """), {"schema": schema_name}).mappings().all()

        dropped = []
        for row in tables:
            table_name = row["table_name"]
            if table_name.startswith("core_"):
                continue
            if table_name.startswith("alembic_version"):
                continue
            try:
                db.execute(text(f'DROP TABLE IF EXISTS "{schema_name}"."{table_name}" CASCADE'))
                dropped.append(table_name)
            except Exception:
                db.rollback()
                raise

        db.commit()
        return dropped

    @staticmethod
    def terminate_db_connections(db: Session) -> int:
        """
        Terminate other connections to the current database.
        Returns number of terminated backends.
        """
        pids = db.execute(text("""
            SELECT pid
            FROM pg_stat_activity
            WHERE datname = current_database()
              AND pid <> pg_backend_pid()
        """)).mappings().all()

        terminated = 0
        for row in pids:
            pid = row["pid"]
            result = db.execute(text("SELECT pg_terminate_backend(:pid)"), {"pid": pid}).scalar()
            if result:
                terminated += 1

        db.commit()
        return terminated

    @staticmethod
    def terminate_schema_connections(db: Session, schema_name: str) -> int:
        """
        Terminate connections that hold locks on objects in the given schema.
        Returns number of terminated backends.
        """
        # Validate schema name
        if not schema_name.replace('_', '').replace('-', '').isalnum():
            raise ValueError(f"Invalid schema name: {schema_name}")

        pids = db.execute(text("""
            SELECT DISTINCT a.pid
            FROM pg_stat_activity a
            JOIN pg_locks l ON l.pid = a.pid
            JOIN pg_class c ON c.oid = l.relation
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE a.datname = current_database()
              AND a.pid <> pg_backend_pid()
              AND n.nspname = :schema
        """), {"schema": schema_name}).mappings().all()

        terminated = 0
        for row in pids:
            pid = row["pid"]
            result = db.execute(text("SELECT pg_terminate_backend(:pid)"), {"pid": pid}).scalar()
            if result:
                terminated += 1

        db.commit()
        return terminated

    @staticmethod
    def get_user_tenants(user_id: int, db: Session) -> List[Dict]:
        """
        Get all tenants accessible by a user.

        Args:
            user_id: User ID
            db: Database session

        Returns:
            List of tenant dictionaries with access info
        """
        user_tenants = db.query(UserTenant, Tenant).join(
            Tenant, UserTenant.tenant_id == Tenant.id
        ).filter(
            UserTenant.user_id == user_id,
            Tenant.active == True
        ).all()

        return [
            {
                "id": tenant.id,
                "schema_name": tenant.schema_name,
                "nome_display": tenant.nome_display,
                "descrizione": tenant.descrizione,
                "active": tenant.active,
                "is_default": user_tenant.is_default,
                "access_granted_at": user_tenant.access_granted_at.isoformat() if user_tenant.access_granted_at else None
            }
            for user_tenant, tenant in user_tenants
        ]

    @staticmethod
    def get_default_tenant(user_id: int, db: Session) -> Optional[Dict]:
        """
        Get user's default tenant.

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Default tenant dict or None
        """
        user_tenants = TenantService.get_user_tenants(user_id, db)

        # Find default
        default = next((t for t in user_tenants if t["is_default"]), None)

        # If no default but only one tenant, use that
        if not default and len(user_tenants) == 1:
            return user_tenants[0]

        return default

    @staticmethod
    def grant_user_access(user_id: int, tenant_id: int, is_default: bool, db: Session) -> UserTenant:
        """
        Grant user access to a tenant.

        Args:
            user_id: User ID
            tenant_id: Tenant ID
            is_default: Whether this is the user's default tenant
            db: Database session

        Returns:
            UserTenant object
        """
        # Check if access already exists
        existing = db.query(UserTenant).filter_by(
            user_id=user_id,
            tenant_id=tenant_id
        ).first()

        if existing:
            # Update existing
            existing.is_default = is_default
            existing.access_revoked_at = None
            db.commit()
            db.refresh(existing)
            return existing

        # Create new access
        user_tenant = UserTenant(
            user_id=user_id,
            tenant_id=tenant_id,
            is_default=is_default
        )
        db.add(user_tenant)
        db.commit()
        db.refresh(user_tenant)
        return user_tenant

    @staticmethod
    def revoke_user_access(user_id: int, tenant_id: int, db: Session):
        """
        Revoke user access to a tenant.

        Args:
            user_id: User ID
            tenant_id: Tenant ID
            db: Database session
        """
        from datetime import datetime

        user_tenant = db.query(UserTenant).filter_by(
            user_id=user_id,
            tenant_id=tenant_id
        ).first()

        if user_tenant:
            user_tenant.access_revoked_at = datetime.utcnow()
            db.commit()

    @staticmethod
    def set_default_tenant(user_id: int, tenant_id: int, db: Session):
        """
        Set a tenant as the default for a user.
        Unsets is_default for all other user's tenants.

        Args:
            user_id: User ID
            tenant_id: Tenant ID to set as default
            db: Database session

        Raises:
            ValueError: If user doesn't have access to this tenant
        """
        # Verify user has access to this tenant
        target_tenant = db.query(UserTenant).filter_by(
            user_id=user_id,
            tenant_id=tenant_id
        ).first()

        if not target_tenant:
            raise ValueError("User does not have access to this tenant")

        # Unset default for all user's tenants
        db.query(UserTenant).filter_by(user_id=user_id).update(
            {"is_default": False},
            synchronize_session=False
        )

        # Set this tenant as default
        target_tenant.is_default = True
        db.commit()
        db.refresh(target_tenant)

    @staticmethod
    def get_enabled_modules(tenant_id: int, db: Session) -> List[str]:
        """
        Get list of enabled module IDs for a tenant.

        Args:
            tenant_id: Tenant ID
            db: Database session

        Returns:
            List of enabled module IDs
        """
        tenant_modules = db.query(TenantModule).filter_by(
            tenant_id=tenant_id
        ).all()

        if not tenant_modules:
            from app.core.module_system.models import Module

            registered_modules = db.query(Module).filter(Module.registered == True).all()
            from app.core.services.tenant_module_service import TenantModuleService

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
            return [module.technical_name for module in registered_modules]

        return [tm.module_id for tm in tenant_modules if tm.enabled]

    @staticmethod
    def is_module_enabled(tenant_id: int, module_id: str, db: Session) -> bool:
        """
        Check if a module is enabled for a tenant.

        Args:
            tenant_id: Tenant ID
            module_id: Module ID
            db: Database session

        Returns:
            True if module is enabled
        """
        tenant_module = db.query(TenantModule).filter_by(
            tenant_id=tenant_id,
            module_id=module_id,
            enabled=True
        ).first()

        return tenant_module is not None

    @staticmethod
    def backup_tenant_schema(schema_name: str, db_config: Dict) -> str:
        """
        Create a backup of tenant schema using pg_dump.

        Args:
            schema_name: The tenant schema name
            db_config: Database configuration (host, port, user, password, database)

        Returns:
            Path to the backup file

        Raises:
            Exception: If backup fails
        """
        # Validate schema name
        if not schema_name.replace('_', '').replace('-', '').isalnum():
            raise ValueError(f"Invalid schema name: {schema_name}")

        # Safety check
        if schema_name.lower() in ['public', 'pg_catalog', 'information_schema']:
            raise ValueError(f"Cannot backup system schema: {schema_name}")

        # Create temporary file for backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_{schema_name}_{timestamp}.sql"
        backup_path = os.path.join(tempfile.gettempdir(), backup_filename)

        # Build pg_dump command
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config.get('password', '')

        cmd = [
            'pg_dump',
            '-h', db_config.get('host', 'localhost'),
            '-p', str(db_config.get('port', 5432)),
            '-U', db_config.get('user', 'postgres'),
            '-d', db_config.get('database', 'postgres'),
            '-n', schema_name,  # Only dump this schema
            '--clean',  # Add DROP statements
            '--if-exists',  # Use IF EXISTS for drops
            '-f', backup_path
        ]

        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )

            return backup_path

        except subprocess.CalledProcessError as e:
            # Clean up failed backup file
            if os.path.exists(backup_path):
                os.remove(backup_path)
            raise Exception(f"Backup failed: {e.stderr}")

    @staticmethod
    def restore_tenant_schema(schema_name: str, backup_file_path: str, db_config: Dict):
        """
        Restore tenant schema from backup file using psql.

        Args:
            schema_name: The tenant schema name to restore
            backup_file_path: Path to the backup SQL file
            db_config: Database configuration

        Raises:
            Exception: If restore fails
        """
        # Validate schema name
        if not schema_name.replace('_', '').replace('-', '').isalnum():
            raise ValueError(f"Invalid schema name: {schema_name}")

        # Safety check
        if schema_name.lower() in ['public', 'pg_catalog', 'information_schema']:
            raise ValueError(f"Cannot restore to system schema: {schema_name}")

        # Verify backup file exists
        if not os.path.exists(backup_file_path):
            raise FileNotFoundError(f"Backup file not found: {backup_file_path}")

        # Build psql command
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config.get('password', '')

        cmd = [
            'psql',
            '-h', db_config.get('host', 'localhost'),
            '-p', str(db_config.get('port', 5432)),
            '-U', db_config.get('user', 'postgres'),
            '-d', db_config.get('database', 'postgres'),
            '-f', backup_file_path
        ]

        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )

        except subprocess.CalledProcessError as e:
            raise Exception(f"Restore failed: {e.stderr}")
