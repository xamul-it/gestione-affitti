"""
Modules API - Expose module configuration to frontend.

Provides endpoints for frontend to discover available modules and their configurations.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.core.database import get_public_db, get_tenant_schema
from app.core.module_system import ModuleRegistry
from app.core.module_system.models import Module
from app.core.module_system.validator import ensure_module_health, check_public_tables
from app.core.module_system.manifest import parse_manifest, validate_manifest, ManifestValidationError
from app.core.auth.dependencies import get_current_user, require_permission
from app.core.auth.models import User
from app.core.models.tenant import Tenant, TenantModule
from app.core.services.tenant_service import TenantService
from app.core.services.tenant_module_service import TenantModuleService
from app.core.platform.models.menu import MenuItem
from app.core.platform.models.dashboard import Widget
from app.core.services.role_registry import RoleRegistry
from app.core.auth.seed_platform_permissions import sync_module_permissions
import logging
from pathlib import Path
import subprocess
import inspect
from sqlalchemy import text
from app.core.module_system.alembic_utils import build_module_alembic_config
import importlib

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/modules", tags=["modules"])


class ModuleToggleRequest(BaseModel):
    """Request to enable/disable a module"""
    enabled: bool


def _load_module_resources(module_record) -> tuple[list, list]:
    menu_items: list = []
    widgets: list = []
    module_name = module_record.technical_name

    try:
        module_obj = importlib.import_module(module_name)
        if hasattr(module_obj, "MENU_ITEMS"):
            menu_items = getattr(module_obj, "MENU_ITEMS") or []
        if hasattr(module_obj, "WIDGETS"):
            widgets = getattr(module_obj, "WIDGETS") or []
    except Exception as e:
        logger.warning("Module resources import failed for %s: %s", module_name, e)

    manifest = module_record.manifest or {}
    if not menu_items:
        menu_items = manifest.get("menu_items", []) or []
    if not widgets:
        widgets = manifest.get("widgets", []) or []

    return menu_items, widgets


def _run_module_alembic_upgrade(module_record) -> bool:
    manifest = module_record.manifest or {}
    schema_target = manifest.get("schema_target")
    if schema_target not in {"public", "public + tenant"}:
        return True

    migrations_path = manifest.get("migrations_path")
    module_prefix = manifest.get("module_short_code")
    if not migrations_path or not module_prefix:
        logger.warning(
            "Module '%s' missing migrations_path/module_short_code for public migrations",
            module_record.technical_name,
        )
        return False

    module_path = Path(module_record.install_path)
    migrations_dir = (module_path / migrations_path).resolve()
    if not migrations_dir.exists():
        logger.warning(
            "Module '%s' migrations_path not found: %s",
            module_record.technical_name,
            migrations_dir,
        )
        return False

    backend_dir = Path(__file__).resolve().parents[4] / "backend"
    config_path = build_module_alembic_config(backend_dir, migrations_dir)
    logger.debug(
        "Module '%s' public migrations: migrations_dir=%s config=%s prefix=%s",
        module_record.technical_name,
        migrations_dir,
        config_path,
        module_prefix,
    )
    try:
        config_preview = config_path.read_text(encoding="utf-8")
        for line in config_preview.splitlines():
            if line.strip().lower().startswith("version_locations") or line.strip() == "[alembic]":
                logger.debug("Alembic config: %s", line)
    except Exception as e:
        logger.debug("Could not read alembic config %s: %s", config_path, e)
    try:
        result = subprocess.run(
            [
                "alembic",
                "-c",
                str(config_path),
                "-x",
                "schema=public",
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

    if result.returncode != 0:
        logger.warning(
            "Module '%s' public migration failed: %s",
            module_record.technical_name,
            result.stderr.strip() or result.stdout.strip(),
        )
        return False
    return True


def _call_seed_entry(module_name: str, entry_point: str, db) -> None:
    if ':' in entry_point:
        module_path, function_name = entry_point.split(':', 1)
    else:
        module_path = entry_point
        function_name = 'register'

    current = importlib.import_module(module_name)
    if module_path:
        try:
            current = importlib.import_module(f"{module_name}.{module_path}")
        except Exception:
            parts = module_path.split('.')
            for part in parts:
                if not hasattr(current, part):
                    raise AttributeError(f"Seed entry point '{entry_point}' not found in module")
                current = getattr(current, part)

    if not hasattr(current, function_name):
        raise AttributeError(f"Seed entry point function '{function_name}' not found in '{module_path}'")

    func = getattr(current, function_name)
    if not callable(func):
        raise TypeError(f"Seed entry point '{entry_point}' is not callable")

    try:
        signature = inspect.signature(func)
    except (TypeError, ValueError):
        func(db)
        return

    if len(signature.parameters) == 0:
        func()
    else:
        func(db)


def _run_module_public_seed(module_record, db: Session) -> bool:
    manifest = module_record.manifest or {}
    schema_target = manifest.get("schema_target")
    if schema_target not in {"public", "public + tenant"}:
        return True

    seeds_path = manifest.get("seeds_path")
    endpoints = manifest.get("endpoints", {}) if isinstance(manifest.get("endpoints"), dict) else {}
    register_endpoint = endpoints.get("register")

    if not seeds_path or not register_endpoint:
        logger.warning(
            "Module '%s' missing seeds_path or endpoints.register for public seeding",
            module_record.technical_name,
        )
        return False

    module_path = Path(module_record.install_path)
    seeds_dir = (module_path / seeds_path).resolve()
    if not seeds_dir.exists():
        logger.warning(
            "Module '%s' seeds_path not found: %s",
            module_record.technical_name,
            seeds_dir,
        )
        return False

    try:
        db.connection().execute(text("SET search_path TO public"))
        _call_seed_entry(module_record.technical_name, register_endpoint, db)
        return True
    except Exception as e:
        db.rollback()
        logger.warning("Module public seed failed for %s: %s", module_record.technical_name, e)
        return False


@router.get("/enabled")
def get_enabled_modules(
    db: Session = Depends(get_public_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema)
) -> List[Dict[str, Any]]:
    """
    Get all visible modules with their frontend configuration.

    Returns module metadata that frontend can use to:
    - Register dynamic routes
    - Add menu items
    - Register extension points
    """
    logger.debug("Modules enabled: tenant_schema=%s", tenant_schema)
    if not tenant_schema:
        logger.debug("Modules enabled: no tenant_schema in request context")
        return []

    registry = ModuleRegistry(db)
    registered_modules = registry.get_registered_modules()
    logger.debug("Modules enabled: platform registered count=%s", len(registered_modules))

    tenant = db.query(Tenant).filter(Tenant.schema_name == tenant_schema).first()
    if not tenant:
        logger.debug("Modules enabled: tenant not found for schema=%s", tenant_schema)
        return []

    tenant_enabled_ids = set(TenantService.get_enabled_modules(tenant.id, db))
    logger.debug(
        "Modules enabled: tenant id=%s schema=%s enabled_ids=%s",
        tenant.id,
        tenant_schema,
        sorted(tenant_enabled_ids),
    )

    registered_modules = db.query(Module).filter(
        Module.registered == True,
        Module.technical_name.in_(tenant_enabled_ids),
    ).all()
    logger.debug("Modules enabled: tenant visible count=%s", len(registered_modules))

    modules_config = []
    has_config = TenantModuleService._config_column_exists(db)
    for module in registered_modules:
        health = ensure_module_health(module, db)
        if not health["ok"]:
            continue
        if module.technical_name not in tenant_enabled_ids:
            continue
        manifest = module.manifest or {}
        module_icon = module.icon or manifest.get("icon") or manifest.get("frontend_config", {}).get("menu_icon")
        tenant_module_config = {}
        if has_config and tenant:
            tenant_module = db.query(TenantModule).filter_by(
                tenant_id=tenant.id,
                module_id=module.technical_name
            ).first()
            tenant_module_config = tenant_module.config if tenant_module else {}

        is_enabled = module.technical_name in tenant_enabled_ids
        config = {
            "technical_name": module.technical_name,
            "name": module.name,
            "version": module.version,
            "icon": module_icon,
            "enabled": is_enabled,
            "state": module.state,
            "tenant_config": tenant_module_config,

            # Frontend configuration from manifest
            "frontend_config": manifest.get("frontend_config", {}),

            # Extension points this module provides
            "extension_points": manifest.get("extension_points", []),

            # Routes this module registers
            "routes": manifest.get("frontend_routes", []),

            # Menu items
            "menu_items": manifest.get("menu_items", []),

            # Permissions exposed by the module
            "permissions": manifest.get("permissions", []),
        }

        modules_config.append(config)

    return modules_config


@router.get("/all")
def get_all_modules(
    db: Session = Depends(get_public_db),
    current_user: User = Depends(require_permission("platform.admin"))
) -> List[Dict[str, Any]]:
    """
    Get ALL modules (enabled and disabled) - Admin only.

    This endpoint is used by the admin console to manage modules.
    """
    registry = ModuleRegistry(db)
    all_modules = registry.get_all_modules()
    tenant_counts = dict(
        db.query(TenantModule.module_id, func.count())
        .filter(TenantModule.enabled == True)
        .group_by(TenantModule.module_id)
        .all()
    )

    modules_list = []
    for module in all_modules:
        health = ensure_module_health(module, db)
        manifest = module.manifest or {}
        module_icon = module.icon or manifest.get("icon") or manifest.get("frontend_config", {}).get("menu_icon")
        module_category = module.category or manifest.get("category") or "other"

        module_info = {
            "technical_name": module.technical_name,
            "name": module.name,
            "version": module.version,
            "description": module.description or manifest.get("description", ""),
            "author": manifest.get("author", ""),
            "icon": module_icon,
            "category": module_category,
            "registered": module.registered,
            "state": module.state,
            "missing_public_tables": health.get("missing", []),
            "dependencies": manifest.get("dependencies", []),
            "tenant_enabled_count": tenant_counts.get(module.technical_name, 0),
            "created_at": module.created_at.isoformat() if module.created_at else None,
            "updated_at": module.updated_at.isoformat() if module.updated_at else None,
        }

        modules_list.append(module_info)

    return modules_list


@router.post("/{technical_name}/toggle")
def toggle_module(
    technical_name: str,
    request: ModuleToggleRequest,
    db: Session = Depends(get_public_db),
    current_user: User = Depends(require_permission("platform.admin"))
):
    """
    Deprecated: platform-level enable/disable is not supported.
    """
    raise HTTPException(
        status_code=400,
        detail="Platform module enable/disable is not supported. Use tenant modules instead."
    )


@router.post("/{technical_name}/register-resources")
def register_module_resources(
    technical_name: str,
    db: Session = Depends(get_public_db),
    current_user: User = Depends(require_permission("platform.admin"))
) -> Dict[str, Any]:
    """
    Force registration for a module:
    - Register menu items and widgets in public
    - Run public migrations + seed
    """
    registry = ModuleRegistry(db)
    module_record = registry.get_module_by_technical_name(technical_name)
    if not module_record:
        raise HTTPException(status_code=404, detail="Module not found")

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
        except ManifestValidationError as e:
            logger.warning("Manifest validation failed for %s: %s", technical_name, e)
        except Exception as e:
            logger.warning("Manifest refresh failed for %s: %s", technical_name, e)

    migrations_ok = False
    try:
        migrations_ok = _run_module_alembic_upgrade(module_record)
    except Exception as e:
        db.rollback()
        logger.warning("Module migrations failed: %s", e)
        migrations_ok = False

    if not migrations_ok:
        module_record.state = "broken"
        module_record.registered = False
        db.commit()
        raise HTTPException(status_code=500, detail="Public migrations failed")

    public_ok, missing_public = check_public_tables(module_record, db)
    if not public_ok:
        module_record.state = "broken"
        module_record.registered = False
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Missing public tables: {', '.join(missing_public)}",
        )

    menu_items, widgets = _load_module_resources(module_record)

    sync_module_permissions(db, manifest)

    menu_registered = 0
    widgets_registered = 0
    tables_ok = 0
    tables_failed = []

    if menu_items:
        db.query(MenuItem).filter(MenuItem.module_id == technical_name).delete()
        for item in menu_items:
            db.add(MenuItem(
                id=item.get("id"),
                module_id=technical_name,
                label=item.get("label"),
                path=item.get("path"),
                icon=item.get("icon"),
                parent_id=item.get("parent_id"),
                order_index=item.get("order_index", 0),
                required_permission=item.get("required_permission"),
                is_domain_data=item.get("is_domain_data", False),
                is_active=item.get("is_active", True),
            ))
            menu_registered += 1
        db.commit()
    else:
        logger.warning("Register resources: empty menu list for module %s", technical_name)

    if widgets:
        db.query(Widget).filter(Widget.module_id == technical_name).delete()
        for widget in widgets:
            db.add(Widget(
                id=widget.get("id"),
                module_id=technical_name,
                title=widget.get("title"),
                component=widget.get("component"),
                description=widget.get("description"),
                default_width=widget.get("default_width", 6),
                default_height=widget.get("default_height", 4),
                category=widget.get("category"),
                required_permission=widget.get("required_permission"),
                is_active=widget.get("is_active", True),
            ))
            widgets_registered += 1
        db.commit()
    else:
        logger.warning("Register resources: empty widget list for module %s", technical_name)

    tenant_modules = db.query(TenantModule).filter(
        TenantModule.module_id == technical_name,
        TenantModule.enabled == True
    ).all()

    module_roles = manifest.get("ruoli_disponibili", []) if manifest else []
    if module_roles:
        mapped_roles = []
        for role in module_roles:
            codice = role.get("technical_name") or role.get("codice")
            if not codice:
                continue
            mapped_roles.append({
                "codice": codice,
                "nome_display": role.get("nome_ruolo") or role.get("nome_display") or codice,
                "descrizione": role.get("descrizione"),
                "tabella_specializzazione": role.get("tabella_specializzazione"),
                "attivo": role.get("attivo", True),
            })
        if mapped_roles:
            RoleRegistry.register_roles(
                db=db,
                modulo_id=technical_name,
                roles=mapped_roles,
                overwrite=True,
            )

    try:
        module_roles_module = importlib.import_module(f"{technical_name}.roles")
        register_roles = getattr(module_roles_module, "register_roles", None)
        if callable(register_roles):
            register_roles(db)
    except Exception as e:
        logger.debug("Module roles registration skipped for %s: %s", technical_name, e)

    seed_ok = _run_module_public_seed(module_record, db)
    if not seed_ok:
        module_record.state = "broken"
        module_record.registered = False
        db.commit()
        raise HTTPException(status_code=500, detail="Public seed failed")

    db.rollback()
    module_record.registered = True
    module_record.registered_at = func.now()
    db.commit()

    return {
        "status": "success",
        "module_id": technical_name,
        "menu_items_registered": menu_registered,
        "widgets_registered": widgets_registered,
        "tenants_processed": 0,
        "tenants_skipped": len(tenant_modules),
        "tables_ok": tables_ok,
        "tables_failed": tables_failed
    }


def trigger_server_reload():
    """
    Trigger a server reload by touching a Python file.
    This works with uvicorn's --reload flag which watches for file changes.
    """
    try:
        import time
        from pathlib import Path

        # Wait for response to be sent first
        time.sleep(0.5)

        # Touch the main.py file to trigger uvicorn reload
        main_file = Path(__file__).parent.parent.parent.parent / "app" / "main.py"

        if main_file.exists():
            # Update the file's modification time
            main_file.touch()
            logger.info(f"Triggered reload by touching {main_file}")
        else:
            logger.error(f"Could not find main.py at {main_file}")

    except Exception as e:
        logger.error(f"Failed to trigger reload: {e}")


@router.post("/reload")
def reload_modules(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_public_db),
    current_user: User = Depends(require_permission("platform.admin"))
):
    """
    Reload all modules at runtime without full server restart.

    This endpoint:
    1. Triggers a graceful reload of the server by touching main.py
    2. All module changes will be applied
    3. Works with uvicorn --reload flag

    Admin only.
    """
    # Schedule reload in background to allow response to be sent first
    background_tasks.add_task(trigger_server_reload)

    logger.info(f"Module reload requested by user {current_user.id}")

    return {
        "success": True,
        "message": "Modifiche salvate. Il server si riavvierà automaticamente.",
        "note": "Il riavvio richiede pochi secondi. La pagina si riconnetterà automaticamente."
    }
