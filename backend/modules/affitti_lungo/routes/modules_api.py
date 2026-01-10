"""
Modules API - Expose module configuration to frontend.

Provides endpoints for frontend to discover enabled modules and their configurations.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.core.database import get_public_db, get_tenant_schema
from app.core.module_system import ModuleRegistry
from app.core.auth.dependencies import get_current_user, require_permission
from app.core.auth.models import User
from app.core.models.tenant import Tenant, TenantModule
from app.core.services.tenant_service import TenantService
from app.core.services.tenant_module_service import TenantModuleService
from app.core.platform.models.menu import MenuItem
from app.core.platform.models.dashboard import Widget
import logging
from pathlib import Path
from alembic import command
from alembic.config import Config
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


def _run_alembic_upgrade() -> None:
    alembic_ini = Path(__file__).resolve().parents[4] / "alembic.ini"
    if not alembic_ini.exists():
        logger.warning("Alembic config not found at %s", alembic_ini)
        return

    config = Config(str(alembic_ini))
    command.upgrade(config, "head")


@router.get("/enabled")
def get_enabled_modules(
    db: Session = Depends(get_public_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema)
) -> List[Dict[str, Any]]:
    """
    Get all enabled modules with their frontend configuration.

    Returns module metadata that frontend can use to:
    - Register dynamic routes
    - Add menu items
    - Register extension points
    """
    logger.debug("Modules enabled: tenant_schema=%s", tenant_schema)
    registry = ModuleRegistry(db)
    enabled_modules = registry.get_enabled_modules()
    logger.debug("Modules enabled: platform enabled count=%s", len(enabled_modules))

    tenant_enabled_ids = None
    tenant = None
    if tenant_schema:
        tenant = db.query(Tenant).filter(Tenant.schema_name == tenant_schema).first()
        if tenant:
            tenant_enabled_ids = set(TenantService.get_enabled_modules(tenant.id, db))
            logger.debug(
                "Modules enabled: tenant id=%s schema=%s enabled_ids=%s",
                tenant.id,
                tenant_schema,
                sorted(tenant_enabled_ids),
            )
        else:
            tenant_enabled_ids = set()
            logger.debug("Modules enabled: tenant not found for schema=%s", tenant_schema)
    else:
        logger.debug("Modules enabled: no tenant_schema in request context")

    modules_config = []
    has_config = TenantModuleService._config_column_exists(db)
    for module in enabled_modules:
        if tenant_enabled_ids is not None and module.technical_name not in tenant_enabled_ids:
            continue
        manifest = module.manifest or {}
        module_icon = module.icon or manifest.get("icon") or manifest.get("frontend_config", {}).get("menu_icon")
        tenant_module_config = {}
        if has_config and tenant_enabled_ids is not None and tenant:
            tenant_module = db.query(TenantModule).filter_by(
                tenant_id=tenant.id,
                module_id=module.technical_name
            ).first()
            tenant_module_config = tenant_module.config if tenant_module else {}

        config = {
            "technical_name": module.technical_name,
            "name": module.name,
            "version": module.version,
            "icon": module_icon,
            "enabled": module.enabled,
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

    modules_list = []
    for module in all_modules:
        manifest = module.manifest or {}
        module_icon = module.icon or manifest.get("icon") or manifest.get("frontend_config", {}).get("menu_icon")

        module_info = {
            "technical_name": module.technical_name,
            "name": module.name,
            "version": module.version,
            "description": module.description or manifest.get("description", ""),
            "author": manifest.get("author", ""),
            "icon": module_icon,
            "enabled": module.enabled,
            "state": module.state,
            "dependencies": manifest.get("dependencies", []),
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
    Enable or disable a module - Admin only.

    This will update the module's enabled status in the database.
    A server restart is required for changes to take effect.
    """
    registry = ModuleRegistry(db)

    try:
        if request.enabled:
            registry.enable_module(technical_name)
            message = f"Module '{technical_name}' enabled successfully"
        else:
            registry.disable_module(technical_name)
            message = f"Module '{technical_name}' disabled successfully"

        return {
            "success": True,
            "message": message,
            "technical_name": technical_name,
            "enabled": request.enabled,
            "restart_required": True
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error toggling module: {str(e)}")


@router.post("/{technical_name}/register-resources")
def register_module_resources(
    technical_name: str,
    db: Session = Depends(get_public_db),
    current_user: User = Depends(require_permission("platform.admin"))
) -> Dict[str, Any]:
    """
    Force registration for a module:
    - Create tenant tables (for enabled tenants)
    - Register menu items and widgets in public
    """
    registry = ModuleRegistry(db)
    module_record = registry.get_module_by_technical_name(technical_name)
    if not module_record:
        raise HTTPException(status_code=404, detail="Module not found")

    try:
        _run_alembic_upgrade()
    except Exception as e:
        logger.warning("Alembic upgrade failed: %s", e)

    menu_items, widgets = _load_module_resources(module_record)

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

    for tm in tenant_modules:
        try:
            TenantModuleService.sync_module_tables_for_tenant(tm.tenant_id, technical_name, db)
            tables_ok += 1
        except Exception as e:
            tables_failed.append({"tenant_id": tm.tenant_id, "error": str(e)})

    if technical_name == "anagrafica_italiana":
        try:
            from anagrafica_italiana.seeds import seed_tipi_documento, seed_stati_documento
            seed_tipi_documento(db)
            seed_stati_documento(db)
        except Exception as e:
            logger.warning("Seed anagrafica domini failed: %s", e)

    return {
        "status": "success",
        "module_id": technical_name,
        "menu_items_registered": menu_registered,
        "widgets_registered": widgets_registered,
        "tenants_processed": len(tenant_modules),
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
