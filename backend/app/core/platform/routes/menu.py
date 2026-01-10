"""
Menu API Routes

API per la gestione del menu dinamico della piattaforma.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging

from app.core.database import get_public_db, get_tenant_schema
from app.core.auth.dependencies import get_current_user
from app.core.auth.models import User
from app.core.platform.models.menu import MenuItem
from app.core.models.tenant import Tenant
from app.core.services.tenant_service import TenantService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/platform/menu", tags=["Platform - Menu"])


# Pydantic Schemas
class MenuItemResponse(BaseModel):
    """Schema response per menu item"""
    id: str
    module_id: str
    label: str
    path: str
    icon: Optional[str] = None
    parent_id: Optional[str] = None
    order_index: int
    required_permission: Optional[str] = None
    is_domain_data: bool = False
    children: List['MenuItemResponse'] = []

    class Config:
        from_attributes = True


# Allow forward reference
MenuItemResponse.model_rebuild()


class MenuItemCreate(BaseModel):
    """Schema per creazione menu item"""
    id: str
    label: str
    path: str
    icon: Optional[str] = None
    parent_id: Optional[str] = None
    order_index: int = 0
    required_permission: Optional[str] = None
    is_domain_data: bool = False


class MenuRegisterRequest(BaseModel):
    """Schema per registrazione batch menu items"""
    module_id: str
    items: List[MenuItemCreate]


@router.get("/", response_model=List[MenuItemResponse])
def get_menu(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_public_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema)
):
    """
    Ritorna menu dinamico filtrato per permessi utente corrente.

    Il menu viene costruito dinamicamente da tutti i moduli registrati
    e filtrato in base ai permessi dell'utente corrente.
    Esclude automaticamente i menu items dei moduli disabilitati.

    Returns:
        List[MenuItemResponse]: Lista di menu items (albero gerarchico)
    """

    # Import here to avoid circular dependency
    from app.core.module_system.models import Module

    # 1. Ottieni lista di module_id abilitati (per-tenant se disponibile)
    enabled_module_ids = None
    if tenant_schema:
        tenant = db.query(Tenant).filter(Tenant.schema_name == tenant_schema).first()
        if tenant:
            enabled_module_ids = set(TenantService.get_enabled_modules(tenant.id, db))
        else:
            enabled_module_ids = set()
    if enabled_module_ids is None:
        enabled_modules = db.query(Module.technical_name).filter(
            Module.enabled == True
        ).all()
        enabled_module_ids = {m[0] for m in enabled_modules}

    logger.debug(f"Enabled modules: {enabled_module_ids}")

    # 2. Carica tutti menu items attivi dei moduli abilitati (+ piattaforma)
    all_items = db.query(MenuItem).filter(
        MenuItem.is_active == True
    ).all()

    # Filtra solo items di moduli abilitati o items di piattaforma (module_id='platform')
    all_items = [
        item for item in all_items
        if item.module_id == 'platform' or item.module_id in enabled_module_ids
    ]

    # 3. Ottieni permessi utente corrente
    user_permissions = set()
    for role in current_user.roles:
        for perm in role.permissions:
            # Costruisci permission string (es: "affitti.view_immobile")
            perm_string = f"{perm.resource}.{perm.action}"
            user_permissions.add(perm_string)

    logger.debug(f"User {current_user.username} permissions: {user_permissions}")

    # 4. Filtra menu items per permessi
    allowed_items = []
    for item in all_items:
        # Se non richiede permessi, è visibile a tutti
        if not item.required_permission:
            allowed_items.append(item)
        # Se utente ha il permesso richiesto
        elif item.required_permission in user_permissions:
            allowed_items.append(item)
        # Admin vede tutto
        elif current_user.is_superuser:
            allowed_items.append(item)

    logger.info(f"User {current_user.username} can see {len(allowed_items)}/{len(all_items)} menu items")

    # 5. Costruisci albero gerarchico
    items_dict = {item.id: item for item in allowed_items}
    root_items = []

    for item in allowed_items:
        # Inizializza lista children
        if not hasattr(item, 'children'):
            item.children = []

        if not item.parent_id:
            # Root level item
            root_items.append(item)
        else:
            # Child item: aggiungi al parent se esiste
            parent = items_dict.get(item.parent_id)
            if parent:
                if not hasattr(parent, 'children'):
                    parent.children = []
                parent.children.append(item)
            else:
                # Parent non esiste o non visibile: tratta come root
                logger.warning(f"Menu item {item.id} has parent {item.parent_id} not found/visible")
                root_items.append(item)

    # 6. Ordina per order_index
    root_items.sort(key=lambda x: (x.order_index, x.label))
    for item in allowed_items:
        if hasattr(item, 'children') and item.children:
            item.children.sort(key=lambda x: (x.order_index, x.label))

    return root_items


@router.post("/register")
def register_menu_items(
    request: MenuRegisterRequest,
    db: Session = Depends(get_public_db)
):
    """
    Registra menu items per un modulo.

    Questa API viene chiamata dai moduli al startup per registrare
    le proprie voci di menu. Rimuove eventuali items precedenti
    dello stesso modulo e crea i nuovi.

    Args:
        request: MenuRegisterRequest con module_id e lista items

    Returns:
        dict: Conferma registrazione con conteggio items
    """

    module_id = request.module_id
    items = request.items

    logger.info(f"Registering {len(items)} menu items for module '{module_id}'")

    try:
        # 1. Rimuovi items esistenti del modulo
        deleted_count = db.query(MenuItem).filter(
            MenuItem.module_id == module_id
        ).delete()

        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} existing menu items for module '{module_id}'")

        # 2. Crea nuovi items
        created = []
        for item_data in items:
            menu_item = MenuItem(
                id=item_data.id,
                module_id=module_id,
                label=item_data.label,
                path=item_data.path,
                icon=item_data.icon,
                parent_id=item_data.parent_id,
                order_index=item_data.order_index,
                required_permission=item_data.required_permission,
                is_domain_data=item_data.is_domain_data,
                is_active=True
            )
            db.add(menu_item)
            created.append(menu_item)

        db.commit()

        logger.info(f"✅ Successfully registered {len(created)} menu items for module '{module_id}'")

        return {
            "status": "success",
            "module_id": module_id,
            "items_registered": len(created),
            "items_deleted": deleted_count
        }

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to register menu items for module '{module_id}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register menu items: {str(e)}"
        )


@router.delete("/{module_id}")
def unregister_menu_items(
    module_id: str,
    db: Session = Depends(get_public_db)
):
    """
    Rimuove tutti i menu items di un modulo.

    Utile quando un modulo viene disinstallato.

    Args:
        module_id: ID del modulo

    Returns:
        dict: Conferma rimozione con conteggio
    """

    deleted_count = db.query(MenuItem).filter(
        MenuItem.module_id == module_id
    ).delete()

    db.commit()

    logger.info(f"Unregistered {deleted_count} menu items for module '{module_id}'")

    return {
        "status": "success",
        "module_id": module_id,
        "items_deleted": deleted_count
    }


@router.get("/modules", response_model=List[str])
def get_modules_with_menu(
    db: Session = Depends(get_public_db)
):
    """
    Ritorna lista di module_id che hanno registrato menu items.

    Returns:
        List[str]: Lista module IDs
    """

    results = db.query(MenuItem.module_id).distinct().all()
    module_ids = [r[0] for r in results]

    return module_ids


@router.get("/domain-data")
def get_domain_data_menu(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_public_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema)
):
    """
    Ritorna menu items che sono dati di dominio/riferimento, organizzati per modulo.

    Questi items vengono mostrati sia:
    - Nel menu del modulo sotto il separatore "Domini"
    - Nella pagina "Amministrazione Dati"

    Returns:
        dict: Struttura {module_id: {module_name: str, items: [...]}}
    """

    # Import here to avoid circular dependency
    from app.core.module_system.models import Module

    # 1. Ottieni moduli abilitati (per-tenant se disponibile)
    enabled_module_ids = None
    if tenant_schema:
        tenant = db.query(Tenant).filter(Tenant.schema_name == tenant_schema).first()
        if tenant:
            enabled_module_ids = set(TenantService.get_enabled_modules(tenant.id, db))
        else:
            enabled_module_ids = set()
    if enabled_module_ids is None:
        enabled_modules_query = db.query(Module).filter(Module.enabled == True).all()
    else:
        enabled_modules_query = db.query(Module).filter(
            Module.technical_name.in_(enabled_module_ids)
        ).all()
    modules_map = {m.technical_name: m.name for m in enabled_modules_query}

    # 2. Carica domain data menu items attivi
    domain_items = db.query(MenuItem).filter(
        MenuItem.is_active == True,
        MenuItem.is_domain_data == True
    ).order_by(MenuItem.module_id, MenuItem.order_index).all()

    # 3. Filtra per moduli abilitati
    domain_items = [
        item for item in domain_items
        if item.module_id in modules_map
    ]

    # 4. Raggruppa per modulo
    result = {}
    for item in domain_items:
        module_id = item.module_id
        if module_id not in result:
            result[module_id] = {
                "module_id": module_id,
                "module_name": modules_map.get(module_id, module_id),
                "items": []
            }

        result[module_id]["items"].append({
            "id": item.id,
            "label": item.label,
            "path": item.path,
            "icon": item.icon,
            "description": f"Gestione {item.label}",
        })

    logger.info(f"Returning domain data menu for {len(result)} modules with {sum(len(m['items']) for m in result.values())} total items")

    return result
