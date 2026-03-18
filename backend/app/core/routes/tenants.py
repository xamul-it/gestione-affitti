"""
API endpoints for tenant management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
import tempfile

from app.core.database import get_db
from app.core.auth.dependencies import get_current_user, require_permission
from app.core.auth.models import User
from app.core.models.tenant import Tenant, UserTenant
from app.core.config import settings
from app.core.schemas.tenant import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantWithAccessResponse,
    GrantTenantAccessRequest,
    SwitchTenantRequest,
    TenantModuleResponse,
    InstallModuleRequest,
    UninstallModuleRequest,
    TenantModuleConfigUpdate
)
from app.core.services.tenant_service import TenantService
from app.core.services.tenant_module_service import TenantModuleService

router = APIRouter(prefix="/tenants", tags=["Tenants"])


def ensure_tenant_admin_access(tenant_id: int, current_user: User, db: Session) -> None:
    if current_user.is_superuser or current_user.has_permission("platform.admin"):
        return

    if not current_user.has_permission("tenant.admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Required: tenant.admin"
        )

    access = db.query(UserTenant).filter_by(
        user_id=current_user.id,
        tenant_id=tenant_id
    ).first()
    if not access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant"
        )


# ============================================================================
# Tenant CRUD Operations
# ============================================================================

@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(
    tenant_data: TenantCreate,
    current_user: User = Depends(require_permission("platform.admin")),
    db: Session = Depends(get_db)
):
    """
    Create new tenant - PLATFORM ADMIN ONLY.

    Creates a new tenant with its own PostgreSQL schema.
    """
    # Check if schema name already exists
    existing = db.query(Tenant).filter_by(schema_name=tenant_data.schema_name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant with schema '{tenant_data.schema_name}' already exists"
        )

    # Create tenant record
    tenant = Tenant(
        schema_name=tenant_data.schema_name,
        nome_display=tenant_data.nome_display,
        descrizione=tenant_data.descrizione
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    # Create schema
    try:
        TenantService.create_tenant_schema(tenant, db)
    except Exception as e:
        # Rollback tenant creation if schema creation fails
        db.delete(tenant)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create schema: {str(e)}"
        )

    return tenant


@router.get("/", response_model=List[TenantResponse])
def list_tenants(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    current_user: User = Depends(require_permission("platform.admin")),
    db: Session = Depends(get_db)
):
    """
    List all tenants - PLATFORM ADMIN ONLY.
    """
    query = db.query(Tenant)

    if active_only:
        query = query.filter(Tenant.active == True)

    tenants = query.offset(skip).limit(limit).all()
    return tenants


# ============================================================================
# User-Tenant Access Management
# ============================================================================
# IMPORTANT: These specific routes must come BEFORE /{tenant_id} routes
# to avoid FastAPI matching "my-tenants" as a tenant_id parameter

@router.get("/my-tenants", response_model=List[TenantWithAccessResponse])
def get_my_tenants(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all tenants accessible by current user.
    """
    return TenantService.get_user_tenants(current_user.id, db)


@router.get("/my-tenants/default", response_model=TenantWithAccessResponse)
def get_default_tenant(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's default tenant.

    If user has only one tenant, returns that.
    If user has multiple tenants, returns the one marked as default.
    """
    tenant = TenantService.get_default_tenant(current_user.id, db)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No default tenant found"
        )
    return tenant


@router.post("/switch")
def switch_tenant(
    request: SwitchTenantRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Switch to a different tenant (returns new JWT token with tenant context).
    """
    # Verify user has access to this tenant
    tenants = TenantService.get_user_tenants(current_user.id, db)
    tenant = next((t for t in tenants if t["id"] == request.tenant_id), None)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant"
        )

    # Create new token with tenant_schema
    from app.core.auth.security import create_access_token, create_refresh_token
    access_token = create_access_token(
        data={"sub": str(current_user.id), "username": current_user.username},
        tenant_schema=tenant["schema_name"]
    )
    refresh_token = create_refresh_token(
        data={
            "sub": str(current_user.id),
            "username": current_user.username,
            "tenant_schema": tenant["schema_name"]
        }
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "tenant": tenant
    }


@router.post("/set-default/{tenant_id}")
def set_default_tenant(
    tenant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set a tenant as the default for the current user.
    """
    try:
        TenantService.set_default_tenant(current_user.id, tenant_id, db)
        return {"status": "success", "message": "Default tenant updated"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


# ============================================================================
# Tenant CRUD Operations (with path parameters)
# ============================================================================

@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(
    tenant_id: int,
    current_user: User = Depends(require_permission("platform.admin")),
    db: Session = Depends(get_db)
):
    """
    Get tenant by ID - PLATFORM ADMIN ONLY.
    """
    tenant = db.query(Tenant).get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: int,
    tenant_update: TenantUpdate,
    current_user: User = Depends(require_permission("platform.admin")),
    db: Session = Depends(get_db)
):
    """
    Update tenant - PLATFORM ADMIN ONLY.
    """
    tenant = db.query(Tenant).get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Update fields
    update_data = tenant_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)

    db.commit()
    db.refresh(tenant)
    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(
    tenant_id: int,
    drop_schema: bool = False,
    current_user: User = Depends(require_permission("platform.admin")),
    db: Session = Depends(get_db)
):
    """
    Delete tenant - PLATFORM ADMIN ONLY.

    By default, keeps the schema and data (soft delete tenant record only).
    Set drop_schema=true to also drop the PostgreSQL schema (IRREVERSIBLE).
    """
    tenant = db.query(Tenant).get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    schema_name = tenant.schema_name

    # Delete tenant record (cascade will delete user_tenants and tenant_modules)
    db.delete(tenant)
    db.commit()

    # Optionally drop schema
    if drop_schema:
        try:
            TenantService.drop_tenant_schema(schema_name, db, cascade=True)
        except Exception as e:
            # Schema deletion failed, but tenant record is already deleted
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Tenant deleted but schema drop failed: {str(e)}"
            )

    return None


@router.post("/{tenant_id}/grant-access")
def grant_user_access(
    tenant_id: int,
    request: GrantTenantAccessRequest,
    current_user: User = Depends(require_permission("platform.admin")),
    db: Session = Depends(get_db)
):
    """
    Grant user access to a tenant - PLATFORM ADMIN ONLY.
    """
    # Verify tenant exists
    tenant = db.query(Tenant).get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Grant access
    user_tenant = TenantService.grant_user_access(
        request.user_id,
        tenant_id,
        request.is_default,
        db
    )

    return {"status": "granted", "user_tenant_id": user_tenant.id}


@router.post("/{tenant_id}/revoke-access/{user_id}")
def revoke_user_access(
    tenant_id: int,
    user_id: int,
    current_user: User = Depends(require_permission("platform.admin")),
    db: Session = Depends(get_db)
):
    """
    Revoke user access to a tenant - PLATFORM ADMIN ONLY.
    """
    TenantService.revoke_user_access(user_id, tenant_id, db)
    return {"status": "revoked"}


# ============================================================================
# Tenant Module Management
# ============================================================================

@router.get("/{tenant_id}/modules", response_model=List[TenantModuleResponse])
def get_tenant_modules(
    tenant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all modules and their status for a tenant - PLATFORM ADMIN ONLY.
    """
    # Verify tenant exists
    tenant = db.query(Tenant).get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    ensure_tenant_admin_access(tenant_id, current_user, db)
    return TenantModuleService.get_tenant_modules(tenant_id, db)


@router.post("/{tenant_id}/modules/install")
def install_module(
    tenant_id: int,
    request: InstallModuleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Install module for tenant - PLATFORM ADMIN ONLY.

    Creates module tables in tenant schema.
    """
    try:
        ensure_tenant_admin_access(tenant_id, current_user, db)
        TenantModuleService.install_module_for_tenant(
            tenant_id,
            request.module_id,
            db,
            seed_test_data=request.seed_test_data,
        )
        return {"status": "installed", "module_id": request.module_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Installation failed: {str(e)}")


@router.post("/{tenant_id}/modules/{module_id}/disable")
def disable_module(
    tenant_id: int,
    module_id: str,
    drop_tables: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disable module (keep data) - PLATFORM ADMIN ONLY.
    """
    ensure_tenant_admin_access(tenant_id, current_user, db)
    drop_result = TenantModuleService.disable_module_for_tenant(
        tenant_id, module_id, db, drop_tables=drop_tables
    )
    return {
        "status": "disabled",
        "module_id": module_id,
        "tables_dropped": drop_result.get("dropped", []),
        "tables_failed": drop_result.get("failed", []),
    }


@router.post("/{tenant_id}/clear-tables")
def clear_tenant_tables(
    tenant_id: int,
    force: bool = False,
    current_user: User = Depends(require_permission("platform.admin")),
    db: Session = Depends(get_db),
):
    """
    Drop all tables in the tenant schema (keeps schema).
    PLATFORM ADMIN ONLY.
    """
    tenant = db.query(Tenant).get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    result = TenantService.clear_tenant_tables(tenant.schema_name, db, force=force)
    return {
        "status": "cleared",
        "tenant_id": tenant_id,
        "tables_dropped": result["dropped"],
        "tables_failed": result["failed"],
    }


@router.delete("/{tenant_id}/modules/{module_id}")
def uninstall_module(
    tenant_id: int,
    module_id: str,
    drop_tables: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Uninstall module and optionally drop its tables - PLATFORM ADMIN ONLY.

    WARNING: Setting drop_tables=true will permanently delete all module data!
    """
    try:
        ensure_tenant_admin_access(tenant_id, current_user, db)
        TenantModuleService.uninstall_module_for_tenant(
            tenant_id, module_id, drop_tables, db
        )
        return {
            "status": "uninstalled",
            "module_id": module_id,
            "tables_dropped": drop_tables
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Uninstallation failed: {str(e)}")


@router.put("/{tenant_id}/modules/{module_id}/config", response_model=TenantModuleResponse)
def update_module_config(
    tenant_id: int,
    module_id: str,
    request: TenantModuleConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update tenant-specific module configuration - PLATFORM ADMIN ONLY.
    """
    try:
        ensure_tenant_admin_access(tenant_id, current_user, db)
        tenant_module = TenantModuleService.update_module_config(
            tenant_id, module_id, request.config, db
        )
        return {
            "module_id": tenant_module.module_id,
            "name": tenant_module.module_id.replace('_', ' ').title(),
            "enabled": tenant_module.enabled,
            "installed_at": tenant_module.installed_at.isoformat() if tenant_module.installed_at else None,
            "table_count": len(TenantModuleService._get_tenant_tables(tenant_module.module_id)),
            "config": tenant_module.config or {}
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Config update failed: {str(e)}")


# ============================================================================
# Tenant Backup & Restore
# ============================================================================

@router.post("/{tenant_id}/backup")
def backup_tenant(
    tenant_id: int,
    current_user: User = Depends(require_permission("platform.admin")),
    db: Session = Depends(get_db)
):
    """
    Create and download a backup of tenant database - PLATFORM ADMIN ONLY.

    Returns a SQL dump file of the tenant schema.
    """
    # Verify tenant exists
    tenant = db.query(Tenant).get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Parse DATABASE_URL to get connection details
    import re
    db_url = settings.DATABASE_URL
    # Format: postgresql://user:password@host:port/database
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
    if not match:
        raise HTTPException(
            status_code=500,
            detail="Invalid DATABASE_URL format"
        )

    user, password, host, port, database = match.groups()
    db_config = {
        'user': user,
        'password': password,
        'host': host,
        'port': int(port),
        'database': database
    }

    try:
        backup_path = TenantService.backup_tenant_schema(
            tenant.schema_name,
            db_config
        )

        # Return file for download
        return FileResponse(
            path=backup_path,
            filename=f"backup_{tenant.schema_name}_{tenant.nome_display.replace(' ', '_')}.sql",
            media_type='application/sql',
            background=None  # File will be deleted after download by cleanup
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Backup failed: {str(e)}"
        )


@router.post("/{tenant_id}/restore")
async def restore_tenant(
    tenant_id: int,
    backup_file: UploadFile = File(...),
    current_user: User = Depends(require_permission("platform.admin")),
    db: Session = Depends(get_db)
):
    """
    Restore tenant database from backup file - PLATFORM ADMIN ONLY.

    Upload a SQL dump file to restore the tenant schema.
    WARNING: This will overwrite all existing data in the tenant schema!
    """
    # Verify tenant exists
    tenant = db.query(Tenant).get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Validate file type
    if not backup_file.filename.endswith('.sql'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .sql files are accepted"
        )

    # Save uploaded file to temporary location
    temp_file_path = os.path.join(tempfile.gettempdir(), f"restore_{tenant.schema_name}_{backup_file.filename}")

    try:
        # Write uploaded file to disk
        with open(temp_file_path, 'wb') as f:
            content = await backup_file.read()
            f.write(content)

        # Parse DATABASE_URL
        import re
        db_url = settings.DATABASE_URL
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
        if not match:
            raise HTTPException(
                status_code=500,
                detail="Invalid DATABASE_URL format"
            )

        user, password, host, port, database = match.groups()
        db_config = {
            'user': user,
            'password': password,
            'host': host,
            'port': int(port),
            'database': database
        }

        # Restore from backup
        TenantService.restore_tenant_schema(
            tenant.schema_name,
            temp_file_path,
            db_config
        )

        return {
            "status": "restored",
            "tenant_id": tenant_id,
            "schema_name": tenant.schema_name,
            "backup_file": backup_file.filename
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Restore failed: {str(e)}"
        )

    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
