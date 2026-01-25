"""
Dashboard API Routes

API per la gestione della dashboard e widget della piattaforma.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from app.core.database import get_public_db, get_tenant_schema
from app.core.auth.dependencies import get_current_user
from app.core.auth.models import User
from app.core.models.tenant import Tenant
from app.core.services.tenant_service import TenantService
from app.core.platform.models.dashboard import Widget, UserDashboard

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/platform/dashboard", tags=["Platform - Dashboard"])


# Pydantic Schemas
class WidgetResponse(BaseModel):
    """Schema response per widget"""
    id: str
    module_id: str
    title: str
    component: str
    description: Optional[str] = None
    default_width: int
    default_height: int
    category: Optional[str] = None

    class Config:
        from_attributes = True


class DashboardLayoutItem(BaseModel):
    """Schema per item nel layout dashboard"""
    i: str  # widget id
    x: int
    y: int
    w: int  # width
    h: int  # height


class DashboardResponse(BaseModel):
    """Schema response per dashboard completa"""
    layout: List[DashboardLayoutItem]
    widgets: List[WidgetResponse]


class WidgetCreate(BaseModel):
    """Schema per creazione widget"""
    id: str
    title: str
    component: str
    description: Optional[str] = None
    default_width: int = 6
    default_height: int = 4
    category: Optional[str] = None
    required_permission: Optional[str] = None


class WidgetRegisterRequest(BaseModel):
    """Schema per registrazione batch widget"""
    module_id: str
    widgets: List[WidgetCreate]


@router.get("/my-dashboard", response_model=DashboardResponse)
def get_my_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_public_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema)
):
    """
    Ritorna dashboard personalizzata utente corrente.

    - Se esiste layout salvato, lo ritorna
    - Altrimenti crea layout default con primi 4 widget disponibili
    - Filtra widget per permessi utente

    Returns:
        DashboardResponse: Layout e widget disponibili
    """

    # 1. Ottieni permessi utente corrente
    user_permissions = set()
    for role in current_user.roles:
        for perm in role.permissions:
            perm_string = f"{perm.resource}.{perm.action}"
            user_permissions.add(perm_string)

    logger.debug(f"User {current_user.username} permissions: {user_permissions}")

    # 2. Ottieni lista di module_id abilitati (per-tenant se disponibile)
    from app.core.module_system.models import Module
    enabled_module_ids = None
    if tenant_schema:
        tenant = db.query(Tenant).filter(Tenant.schema_name == tenant_schema).first()
        if tenant:
            enabled_module_ids = set(TenantService.get_enabled_modules(tenant.id, db))
        else:
            enabled_module_ids = set()
    if enabled_module_ids is None:
        enabled_module_ids = set()

    logger.debug(f"Visible modules: {enabled_module_ids}")

    # 3. Carica widget disponibili (filtrati per moduli abilitati e permessi)
    all_widgets = db.query(Widget).filter(Widget.is_active == True).all()

    # Filtra solo widget di moduli abilitati o piattaforma
    all_widgets = [
        widget for widget in all_widgets
        if widget.module_id == 'platform' or widget.module_id in enabled_module_ids
    ]

    available_widgets = []
    for widget in all_widgets:
        # Se non richiede permessi, visibile a tutti
        if not widget.required_permission:
            available_widgets.append(widget)
        # Se utente ha il permesso richiesto
        elif widget.required_permission in user_permissions:
            available_widgets.append(widget)
        # Admin vede tutto
        elif current_user.is_superuser:
            available_widgets.append(widget)

    logger.info(f"Available widgets for user {current_user.username}: {len(available_widgets)}")

    # 4. Carica o crea layout utente
    user_dashboard = db.query(UserDashboard).filter(
        UserDashboard.user_id == current_user.id
    ).first()

    if user_dashboard:
        # Layout esistente
        layout = user_dashboard.layout
        logger.info(f"Loaded existing layout for user {current_user.id}")
    else:
        # Crea layout default con primi 4 widget
        layout = []
        x, y = 0, 0

        for i, widget in enumerate(available_widgets[:4]):
            layout.append({
                'i': widget.id,
                'x': x,
                'y': y,
                'w': widget.default_width,
                'h': widget.default_height
            })
            x += widget.default_width
            if x >= 12:  # Grid 12 colonne
                x = 0
                y += widget.default_height

        # Salva layout default
        if layout:  # Solo se ci sono widget
            user_dashboard = UserDashboard(
                user_id=current_user.id,
                layout=layout
            )
            db.add(user_dashboard)
            db.commit()
            logger.info(f"Created default layout for user {current_user.id} with {len(layout)} widgets")
        else:
            logger.warning(f"No widgets available for user {current_user.id}")

    return {
        'layout': layout,
        'widgets': available_widgets
    }


@router.post("/save-layout")
def save_dashboard_layout(
    layout: List[DashboardLayoutItem],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_public_db)
):
    """
    Salva layout dashboard modificato dall'utente.

    Args:
        layout: Nuovo layout da salvare

    Returns:
        dict: Conferma operazione
    """

    user_dashboard = db.query(UserDashboard).filter(
        UserDashboard.user_id == current_user.id
    ).first()

    layout_data = [item.dict() for item in layout]

    if user_dashboard:
        user_dashboard.layout = layout_data
        user_dashboard.updated_at = datetime.utcnow()
        # IMPORTANTE: Flag per dire a SQLAlchemy che il campo JSON è cambiato
        flag_modified(user_dashboard, 'layout')
        logger.info(f"Updated layout for user {current_user.id}")
    else:
        user_dashboard = UserDashboard(
            user_id=current_user.id,
            layout=layout_data
        )
        db.add(user_dashboard)
        logger.info(f"Created new layout for user {current_user.id}")

    db.commit()

    return {
        "status": "saved",
        "items_count": len(layout_data)
    }


@router.post("/register-widgets")
def register_widgets(
    request: WidgetRegisterRequest,
    db: Session = Depends(get_public_db)
):
    """
    Registra widget per un modulo (chiamata da modulo al startup).

    Args:
        request: Richiesta con module_id e lista widget

    Returns:
        dict: Conferma registrazione
    """
    if not request.widgets:
        logger.warning(f"Skipped widget registration for module {request.module_id}: empty widget list")
        return {
            "status": "skipped",
            "module_id": request.module_id,
            "widgets_registered": 0,
            "widgets_deleted": 0
        }

    # Rimuovi widget esistenti del modulo
    deleted = db.query(Widget).filter(Widget.module_id == request.module_id).delete()
    logger.info(f"Deleted {deleted} existing widgets for module {request.module_id}")

    # Crea nuovi widget
    created = []
    for widget_data in request.widgets:
        widget = Widget(
            id=widget_data.id,
            module_id=request.module_id,
            title=widget_data.title,
            component=widget_data.component,
            description=widget_data.description,
            default_width=widget_data.default_width,
            default_height=widget_data.default_height,
            category=widget_data.category,
            required_permission=widget_data.required_permission
        )
        db.add(widget)
        created.append(widget)

    db.commit()

    logger.info(f"✅ Registered {len(created)} widgets for module {request.module_id}")

    return {
        "status": "success",
        "module_id": request.module_id,
        "widgets_registered": len(created),
        "widgets_deleted": deleted
    }


@router.get("/available-widgets", response_model=List[WidgetResponse])
def get_available_widgets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_public_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema)
):
    """
    Ritorna lista di tutti i widget disponibili per l'utente corrente.
    Utile per UI di configurazione dashboard.

    Returns:
        List[WidgetResponse]: Widget disponibili
    """

    # Ottieni permessi utente
    user_permissions = set()
    for role in current_user.roles:
        for perm in role.permissions:
            user_permissions.add(f"{perm.resource}.{perm.action}")

    # Ottieni lista di module_id abilitati (per-tenant se disponibile)
    from app.core.module_system.models import Module
    enabled_module_ids = None
    if tenant_schema:
        tenant = db.query(Tenant).filter(Tenant.schema_name == tenant_schema).first()
        if tenant:
            enabled_module_ids = set(TenantService.get_enabled_modules(tenant.id, db))
        else:
            enabled_module_ids = set()
    if enabled_module_ids is None:
        enabled_module_ids = set()

    # Filtra widget per moduli abilitati e permessi
    all_widgets = db.query(Widget).filter(Widget.is_active == True).all()

    # Filtra solo widget di moduli abilitati o piattaforma
    all_widgets = [
        widget for widget in all_widgets
        if widget.module_id == 'platform' or widget.module_id in enabled_module_ids
    ]

    available_widgets = []
    for widget in all_widgets:
        if not widget.required_permission:
            available_widgets.append(widget)
        elif widget.required_permission in user_permissions:
            available_widgets.append(widget)
        elif current_user.is_superuser:
            available_widgets.append(widget)

    return available_widgets


class AddWidgetRequest(BaseModel):
    """Schema per aggiunta widget a dashboard"""
    widget_id: str


@router.post("/add-widget")
def add_widget_to_dashboard(
    request: AddWidgetRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_public_db)
):
    """
    Aggiunge un widget alla dashboard dell'utente.

    - Verifica che il widget esista ed è disponibile per l'utente
    - Posiziona il widget automaticamente nel prossimo spazio libero
    - Salva il layout aggiornato

    Args:
        request: Richiesta con widget_id da aggiungere

    Returns:
        dict: Nuovo layout aggiornato
    """

    # 1. Verifica widget esiste
    widget = db.query(Widget).filter(
        Widget.id == request.widget_id,
        Widget.is_active == True
    ).first()

    if not widget:
        raise HTTPException(status_code=404, detail="Widget non trovato")

    # 2. Verifica permessi utente per questo widget
    if widget.required_permission:
        user_permissions = set()
        for role in current_user.roles:
            for perm in role.permissions:
                user_permissions.add(f"{perm.resource}.{perm.action}")

        if widget.required_permission not in user_permissions and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Non hai i permessi per questo widget")

    # 3. Carica dashboard utente
    user_dashboard = db.query(UserDashboard).filter(
        UserDashboard.user_id == current_user.id
    ).first()

    if not user_dashboard:
        # Crea nuova dashboard
        layout = []
        user_dashboard = UserDashboard(
            user_id=current_user.id,
            layout=layout
        )
        db.add(user_dashboard)
    else:
        layout = user_dashboard.layout or []

    # 4. Verifica se widget già presente
    widget_ids = [item['i'] for item in layout]
    if request.widget_id in widget_ids:
        raise HTTPException(status_code=400, detail="Widget già presente nella dashboard")

    # 5. Calcola posizione per nuovo widget
    # Trova il massimo y + h per posizionare sotto tutti gli altri
    max_bottom = 0
    for item in layout:
        bottom = item['y'] + item['h']
        if bottom > max_bottom:
            max_bottom = bottom

    # 6. Aggiungi widget al layout
    new_item = {
        'i': widget.id,
        'x': 0,
        'y': max_bottom,
        'w': widget.default_width,
        'h': widget.default_height
    }
    layout.append(new_item)

    # 7. Salva layout aggiornato
    user_dashboard.layout = layout
    user_dashboard.updated_at = datetime.utcnow()

    # IMPORTANTE: Flag per dire a SQLAlchemy che il campo JSON è cambiato
    flag_modified(user_dashboard, 'layout')

    db.commit()

    logger.info(f"Added widget {widget.id} to dashboard for user {current_user.id}")

    return {
        "status": "success",
        "widget_added": widget.id,
        "layout": layout
    }


@router.delete("/remove-widget/{widget_id}")
def remove_widget_from_dashboard(
    widget_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_public_db)
):
    """
    Rimuove un widget dalla dashboard dell'utente.

    Args:
        widget_id: ID del widget da rimuovere

    Returns:
        dict: Layout aggiornato
    """

    # 1. Carica dashboard utente
    user_dashboard = db.query(UserDashboard).filter(
        UserDashboard.user_id == current_user.id
    ).first()

    if not user_dashboard:
        raise HTTPException(status_code=404, detail="Dashboard non trovata")

    layout = user_dashboard.layout or []

    # 2. Rimuovi widget dal layout
    original_length = len(layout)
    layout = [item for item in layout if item['i'] != widget_id]

    if len(layout) == original_length:
        raise HTTPException(status_code=404, detail="Widget non presente nella dashboard")

    # 3. Salva layout aggiornato
    user_dashboard.layout = layout
    user_dashboard.updated_at = datetime.utcnow()

    # IMPORTANTE: Flag per dire a SQLAlchemy che il campo JSON è cambiato
    flag_modified(user_dashboard, 'layout')

    db.commit()

    logger.info(f"Removed widget {widget_id} from dashboard for user {current_user.id}")

    return {
        "status": "success",
        "widget_removed": widget_id,
        "layout": layout
    }
