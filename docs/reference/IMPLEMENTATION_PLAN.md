# 🚀 Piano Implementazione Platform Features

**Approccio:** FastAPI per tutto, pragmatico, senza over-engineering
**Team:** Platform separato da Moduli
**Timeline:** 3-4 settimane

---

## 1. Menu Dinamico (Priorità ALTA)

### Obiettivo
Permettere ai moduli di registrare voci di menu che vengono composte dinamicamente nel frontend.

### Struttura Database

```sql
-- Tabella menu items registrati dai moduli
CREATE TABLE platform_menu_items (
    id VARCHAR(100) PRIMARY KEY,
    module_id VARCHAR(100) NOT NULL,
    label VARCHAR(200) NOT NULL,
    path VARCHAR(500) NOT NULL,
    icon VARCHAR(50),
    parent_id VARCHAR(100),  -- Per sottomenu
    order_index INTEGER DEFAULT 0,
    required_permission VARCHAR(100),  -- Singolo permesso (semplificato)
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_menu_module ON platform_menu_items(module_id);
CREATE INDEX idx_menu_parent ON platform_menu_items(parent_id);
CREATE INDEX idx_menu_order ON platform_menu_items(order_index);
```

### Backend Implementation

```python
# backend/app/core/platform/models/menu.py

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class MenuItem(Base):
    """Voce di menu registrata da un modulo"""
    __tablename__ = "platform_menu_items"

    id = Column(String(100), primary_key=True)  # es: "affitti.immobili"
    module_id = Column(String(100), nullable=False)  # es: "affitti_lungo"

    label = Column(String(200), nullable=False)  # es: "Immobili"
    path = Column(String(500), nullable=False)  # es: "/immobili"
    icon = Column(String(50))  # es: "building"

    parent_id = Column(String(100), nullable=True)  # Per submenu
    order_index = Column(Integer, default=0)

    required_permission = Column(String(100), nullable=True)  # es: "affitti.view_immobile"
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)


# backend/app/core/platform/routes/menu.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.auth.dependencies import get_current_user
from app.core.auth.models import User
from app.core.platform.models.menu import MenuItem
from pydantic import BaseModel

router = APIRouter(prefix="/platform/menu", tags=["Platform - Menu"])

class MenuItemResponse(BaseModel):
    id: str
    module_id: str
    label: str
    path: str
    icon: str | None
    parent_id: str | None
    order_index: int
    required_permission: str | None
    children: List['MenuItemResponse'] = []

    class Config:
        from_attributes = True

# Allow forward reference
MenuItemResponse.model_rebuild()


@router.get("/", response_model=List[MenuItemResponse])
def get_menu(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ritorna menu dinamico filtrato per permessi utente corrente

    - Carica tutti i menu items attivi
    - Filtra per permessi utente
    - Costruisce albero gerarchico
    - Ordina per order_index
    """

    # Carica tutti menu items attivi
    all_items = db.query(MenuItem).filter(MenuItem.is_active == True).all()

    # Ottieni permessi utente
    user_permissions = set()
    for role in current_user.roles:
        for perm in role.permissions:
            user_permissions.add(f"{perm.resource}.{perm.action}")

    # Filtra per permessi
    allowed_items = []
    for item in all_items:
        # Se no required_permission, visibile a tutti
        if not item.required_permission:
            allowed_items.append(item)
        # Se utente ha permesso, visibile
        elif item.required_permission in user_permissions:
            allowed_items.append(item)
        # Admin vede tutto
        elif current_user.is_superuser:
            allowed_items.append(item)

    # Costruisci albero gerarchico
    items_dict = {item.id: item for item in allowed_items}
    root_items = []

    for item in allowed_items:
        if not item.parent_id:
            # Root item
            root_items.append(item)
        else:
            # Child item: aggiungi al parent
            parent = items_dict.get(item.parent_id)
            if parent:
                if not hasattr(parent, 'children'):
                    parent.children = []
                parent.children.append(item)

    # Ordina per order_index
    root_items.sort(key=lambda x: x.order_index)
    for item in allowed_items:
        if hasattr(item, 'children'):
            item.children.sort(key=lambda x: x.order_index)

    return root_items


@router.post("/register")
def register_menu_items(
    items: List[dict],
    module_id: str,
    db: Session = Depends(get_db)
):
    """
    Registra menu items per un modulo (chiamata da modulo al startup)

    Body:
    {
        "module_id": "affitti_lungo",
        "items": [
            {
                "id": "affitti.immobili",
                "label": "Immobili",
                "path": "/immobili",
                "icon": "building",
                "order_index": 10,
                "required_permission": "affitti.view_immobile"
            },
            ...
        ]
    }
    """

    # Rimuovi items esistenti del modulo
    db.query(MenuItem).filter(MenuItem.module_id == module_id).delete()

    # Crea nuovi items
    created = []
    for item_data in items:
        item = MenuItem(
            id=item_data['id'],
            module_id=module_id,
            label=item_data['label'],
            path=item_data['path'],
            icon=item_data.get('icon'),
            parent_id=item_data.get('parent_id'),
            order_index=item_data.get('order_index', 0),
            required_permission=item_data.get('required_permission')
        )
        db.add(item)
        created.append(item)

    db.commit()

    return {
        "status": "registered",
        "module_id": module_id,
        "items_count": len(created)
    }
```

### Module Registration (Startup Hook)

```python
# backend/app/modules/affitti_lungo/__init__.py

# Aggiungi al file esistente:

# Menu items da registrare
MENU_ITEMS = [
    {
        "id": "affitti.immobili",
        "label": "Immobili",
        "path": "/immobili",
        "icon": "building",
        "order_index": 10,
        "required_permission": "affitti.view_immobile"
    },
    {
        "id": "affitti.contratti",
        "label": "Contratti",
        "path": "/contratti",
        "icon": "file-contract",
        "order_index": 20,
        "required_permission": "affitti.view_contratto"
    },
    {
        "id": "affitti.affittuari",
        "label": "Affittuari",
        "path": "/affittuari",
        "icon": "users",
        "order_index": 30,
        "required_permission": "affitti.view_affittuario"
    },
    {
        "id": "affitti.proprietari",
        "label": "Proprietari",
        "path": "/proprietari",
        "icon": "user-tie",
        "order_index": 40,
        "required_permission": "affitti.view_proprietario"
    },
    {
        "id": "affitti.condomini",
        "label": "Condomini",
        "path": "/condomini",
        "icon": "building-columns",
        "order_index": 50,
        "required_permission": "affitti.view_condominio"
    },
    {
        "id": "affitti.submenu",
        "label": "Altri",
        "path": "#",
        "icon": "ellipsis-h",
        "order_index": 60,
        "required_permission": None  # Visibile a tutti
    },
    {
        "id": "affitti.spese",
        "label": "Spese",
        "path": "/spese",
        "parent_id": "affitti.submenu",  # Submenu!
        "order_index": 1,
        "required_permission": "affitti.view_spesa"
    },
    {
        "id": "affitti.incassi",
        "label": "Incassi",
        "path": "/incassi",
        "parent_id": "affitti.submenu",
        "order_index": 2,
        "required_permission": "affitti.view_incasso"
    },
]


# backend/app/main.py (modificare startup)

@app.on_event("startup")
async def register_module_menu():
    """Registra menu items del modulo Affitti al startup"""
    from app.modules.affitti_lungo import MENU_ITEMS
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/v1/platform/menu/register",
                params={"module_id": "affitti_lungo"},
                json=MENU_ITEMS
            )
            if response.status_code == 200:
                logger.info(f"✅ Registered {len(MENU_ITEMS)} menu items for affitti_lungo")
            else:
                logger.error(f"❌ Failed to register menu items: {response.text}")
    except Exception as e:
        logger.warning(f"⚠️  Could not register menu items (platform may not be ready): {e}")
```

### Frontend Implementation

```javascript
// frontend/src/components/Layout/DynamicMenu.jsx

import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import axios from 'axios'
import './DynamicMenu.css'

function DynamicMenu() {
  const [menuItems, setMenuItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [expandedItems, setExpandedItems] = useState(new Set())
  const location = useLocation()

  useEffect(() => {
    loadMenu()
  }, [])

  async function loadMenu() {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(
        'http://localhost:8000/api/v1/platform/menu/',
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )
      setMenuItems(response.data)
    } catch (error) {
      console.error('Failed to load menu:', error)
    } finally {
      setLoading(false)
    }
  }

  function toggleExpand(itemId) {
    setExpandedItems(prev => {
      const next = new Set(prev)
      if (next.has(itemId)) {
        next.delete(itemId)
      } else {
        next.add(itemId)
      }
      return next
    })
  }

  function renderMenuItem(item) {
    const hasChildren = item.children && item.children.length > 0
    const isExpanded = expandedItems.has(item.id)
    const isActive = location.pathname === item.path

    return (
      <li key={item.id} className={`menu-item ${hasChildren ? 'has-children' : ''}`}>
        {hasChildren ? (
          <>
            <div
              className={`menu-link ${isExpanded ? 'expanded' : ''}`}
              onClick={() => toggleExpand(item.id)}
            >
              {item.icon && <i className={`icon-${item.icon}`}></i>}
              <span>{item.label}</span>
              <i className={`icon-chevron-${isExpanded ? 'down' : 'right'} submenu-arrow`}></i>
            </div>
            {isExpanded && (
              <ul className="submenu">
                {item.children.map(child => renderMenuItem(child))}
              </ul>
            )}
          </>
        ) : (
          <Link
            to={item.path}
            className={`menu-link ${isActive ? 'active' : ''}`}
          >
            {item.icon && <i className={`icon-${item.icon}`}></i>}
            <span>{item.label}</span>
          </Link>
        )}
      </li>
    )
  }

  if (loading) {
    return <div className="menu-loading">Caricamento menu...</div>
  }

  return (
    <nav className="dynamic-menu">
      <ul className="menu-list">
        {menuItems.map(item => renderMenuItem(item))}
      </ul>
    </nav>
  )
}

export default DynamicMenu
```

```css
/* frontend/src/components/Layout/DynamicMenu.css */

.dynamic-menu {
  width: 250px;
  background: #2c3e50;
  height: 100vh;
  overflow-y: auto;
}

.menu-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.menu-item {
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.menu-link {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  color: #ecf0f1;
  text-decoration: none;
  transition: all 0.3s;
  cursor: pointer;
}

.menu-link:hover {
  background: rgba(255,255,255,0.1);
}

.menu-link.active {
  background: #3498db;
  border-left: 4px solid #2980b9;
}

.menu-link i {
  margin-right: 10px;
  width: 20px;
}

.submenu-arrow {
  margin-left: auto;
  font-size: 12px;
}

.submenu {
  list-style: none;
  padding: 0;
  margin: 0;
  background: rgba(0,0,0,0.2);
}

.submenu .menu-link {
  padding-left: 50px;
  font-size: 14px;
}
```

---

## 2. Dashboard & Widget System (Priorità ALTA)

### Struttura Database

```sql
-- Widgets disponibili
CREATE TABLE platform_widgets (
    id VARCHAR(100) PRIMARY KEY,
    module_id VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    component VARCHAR(200) NOT NULL,  -- Nome componente React
    description TEXT,
    default_width INTEGER DEFAULT 6,  -- Grid 12 colonne
    default_height INTEGER DEFAULT 4,
    category VARCHAR(50),  -- 'stats', 'alerts', 'charts'
    required_permission VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Layout dashboard per utente
CREATE TABLE platform_user_dashboards (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    layout JSON NOT NULL,  -- Array di {i: widget_id, x, y, w, h}
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_widgets_module ON platform_widgets(module_id);
```

### Backend Implementation

```python
# backend/app/core/platform/models/dashboard.py

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class Widget(Base):
    """Widget disponibile per dashboard"""
    __tablename__ = "platform_widgets"

    id = Column(String(100), primary_key=True)
    module_id = Column(String(100), nullable=False)

    title = Column(String(200), nullable=False)
    component = Column(String(200), nullable=False)  # Nome componente React
    description = Column(String(500))

    default_width = Column(Integer, default=6)
    default_height = Column(Integer, default=4)
    category = Column(String(50))

    required_permission = Column(String(100))
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class UserDashboard(Base):
    """Layout dashboard personalizzato per utente"""
    __tablename__ = "platform_user_dashboards"

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    layout = Column(JSON, nullable=False)  # [{i: 'widget_id', x, y, w, h}]
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# backend/app/core/platform/routes/dashboard.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.auth.dependencies import get_current_user
from app.core.auth.models import User
from app.core.platform.models.dashboard import Widget, UserDashboard
from pydantic import BaseModel

router = APIRouter(prefix="/platform/dashboard", tags=["Platform - Dashboard"])

class WidgetResponse(BaseModel):
    id: str
    module_id: str
    title: str
    component: str
    description: str | None
    default_width: int
    default_height: int
    category: str | None

    class Config:
        from_attributes = True


class DashboardLayoutItem(BaseModel):
    i: str  # widget id
    x: int
    y: int
    w: int  # width
    h: int  # height


class DashboardResponse(BaseModel):
    layout: List[DashboardLayoutItem]
    widgets: List[WidgetResponse]


@router.get("/my-dashboard", response_model=DashboardResponse)
def get_my_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ritorna dashboard personalizzata utente corrente

    - Se esiste layout salvato, lo ritorna
    - Altrimenti crea layout default con primi 4 widget disponibili
    - Filtra widget per permessi utente
    """

    # Ottieni permessi utente
    user_permissions = set()
    for role in current_user.roles:
        for perm in role.permissions:
            user_permissions.add(f"{perm.resource}.{perm.action}")

    # Carica widget disponibili (filtrati per permessi)
    all_widgets = db.query(Widget).filter(Widget.is_active == True).all()

    available_widgets = []
    for widget in all_widgets:
        if not widget.required_permission:
            available_widgets.append(widget)
        elif widget.required_permission in user_permissions:
            available_widgets.append(widget)
        elif current_user.is_superuser:
            available_widgets.append(widget)

    # Carica o crea layout utente
    user_dashboard = db.query(UserDashboard).filter(
        UserDashboard.user_id == current_user.id
    ).first()

    if user_dashboard:
        # Layout esistente
        layout = user_dashboard.layout
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
        user_dashboard = UserDashboard(
            user_id=current_user.id,
            layout=layout
        )
        db.add(user_dashboard)
        db.commit()

    return {
        'layout': layout,
        'widgets': available_widgets
    }


@router.post("/save-layout")
def save_dashboard_layout(
    layout: List[DashboardLayoutItem],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Salva layout dashboard modificato dall'utente"""

    user_dashboard = db.query(UserDashboard).filter(
        UserDashboard.user_id == current_user.id
    ).first()

    layout_data = [item.dict() for item in layout]

    if user_dashboard:
        user_dashboard.layout = layout_data
        user_dashboard.updated_at = datetime.utcnow()
    else:
        user_dashboard = UserDashboard(
            user_id=current_user.id,
            layout=layout_data
        )
        db.add(user_dashboard)

    db.commit()

    return {"status": "saved", "items_count": len(layout_data)}


@router.post("/register-widgets")
def register_widgets(
    widgets: List[dict],
    module_id: str,
    db: Session = Depends(get_db)
):
    """
    Registra widget per un modulo (chiamata da modulo al startup)

    Body:
    {
        "module_id": "affitti_lungo",
        "widgets": [
            {
                "id": "affitti.contratti_scadenza",
                "title": "Contratti in Scadenza",
                "component": "ContrattiScadenzaWidget",
                "description": "...",
                "default_width": 6,
                "default_height": 4,
                "category": "alerts"
            }
        ]
    }
    """

    # Rimuovi widget esistenti del modulo
    db.query(Widget).filter(Widget.module_id == module_id).delete()

    # Crea nuovi widget
    created = []
    for widget_data in widgets:
        widget = Widget(
            id=widget_data['id'],
            module_id=module_id,
            title=widget_data['title'],
            component=widget_data['component'],
            description=widget_data.get('description'),
            default_width=widget_data.get('default_width', 6),
            default_height=widget_data.get('default_height', 4),
            category=widget_data.get('category'),
            required_permission=widget_data.get('required_permission')
        )
        db.add(widget)
        created.append(widget)

    db.commit()

    return {
        "status": "registered",
        "module_id": module_id,
        "widgets_count": len(created)
    }
```

### Frontend Dashboard

```javascript
// frontend/src/pages/Dashboard.jsx

import React, { useState, useEffect } from 'react'
import GridLayout from 'react-grid-layout'
import 'react-grid-layout/css/styles.css'
import 'react-resizable/css/styles.css'
import axios from 'axios'
import WidgetLoader from '../components/WidgetLoader'
import './Dashboard.css'

function Dashboard() {
  const [layout, setLayout] = useState([])
  const [widgets, setWidgets] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboard()
  }, [])

  async function loadDashboard() {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(
        'http://localhost:8000/api/v1/platform/dashboard/my-dashboard',
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )
      setLayout(response.data.layout)
      setWidgets(response.data.widgets)
    } catch (error) {
      console.error('Failed to load dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  async function handleLayoutChange(newLayout) {
    setLayout(newLayout)

    // Salva su server (debounced in produzione)
    const token = localStorage.getItem('access_token')
    try {
      await axios.post(
        'http://localhost:8000/api/v1/platform/dashboard/save-layout',
        newLayout,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      )
    } catch (error) {
      console.error('Failed to save layout:', error)
    }
  }

  if (loading) {
    return <div className="loading">Caricamento dashboard...</div>
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <button className="btn-config">
          <i className="icon-cog"></i> Configura Widget
        </button>
      </div>

      <GridLayout
        className="dashboard-grid"
        layout={layout}
        cols={12}
        rowHeight={30}
        width={1200}
        onLayoutChange={handleLayoutChange}
        isDraggable={true}
        isResizable={true}
        compactType="vertical"
      >
        {layout.map(item => {
          const widget = widgets.find(w => w.id === item.i)
          if (!widget) return null

          return (
            <div key={item.i} className="widget-container">
              <div className="widget-header">
                <h3>{widget.title}</h3>
                <div className="widget-actions">
                  <button className="widget-btn" title="Refresh">
                    <i className="icon-refresh"></i>
                  </button>
                  <button className="widget-btn" title="Remove">
                    <i className="icon-times"></i>
                  </button>
                </div>
              </div>
              <div className="widget-body">
                <WidgetLoader widget={widget} />
              </div>
            </div>
          )
        })}
      </GridLayout>
    </div>
  )
}

export default Dashboard
```

```javascript
// frontend/src/components/WidgetLoader.jsx

import React, { lazy, Suspense } from 'react'

// Widget registry (da espandere dinamicamente)
const WIDGET_COMPONENTS = {
  'ContrattiScadenzaWidget': lazy(() => import('../modules/affitti/widgets/ContrattiScadenzaWidget')),
  'AffittiStatsWidget': lazy(() => import('../modules/affitti/widgets/AffittiStatsWidget')),
  // Aggiungi altri widget qui...
}

function WidgetLoader({ widget }) {
  const WidgetComponent = WIDGET_COMPONENTS[widget.component]

  if (!WidgetComponent) {
    return (
      <div className="widget-error">
        <p>Widget non trovato: {widget.component}</p>
      </div>
    )
  }

  return (
    <Suspense fallback={<div className="widget-loading">Caricamento...</div>}>
      <WidgetComponent />
    </Suspense>
  )
}

export default WidgetLoader
```

```javascript
// frontend/src/modules/affitti/widgets/ContrattiScadenzaWidget.jsx

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './ContrattiScadenzaWidget.css'

function ContrattiScadenzaWidget() {
  const [contratti, setContratti] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(
        'http://localhost:8000/api/v1/contratti/',
        {
          params: {
            limit: 5,
            // Filtra contratti che scadono nei prossimi 90 giorni
            data_fine_max: new Date(Date.now() + 90*24*60*60*1000).toISOString().split('T')[0]
          },
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )
      setContratti(response.data)
    } catch (error) {
      console.error('Failed to load contratti:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div>Caricamento...</div>
  }

  return (
    <div className="contratti-widget">
      <div className="widget-stat">
        <span className="stat-number">{contratti.length}</span>
        <span className="stat-label">Contratti in scadenza</span>
      </div>

      <ul className="contratti-list">
        {contratti.map(c => (
          <li key={c.id} className="contratto-item">
            <div className="contratto-info">
              <strong>{c.codice}</strong>
              <span className="contratto-immobile">
                {c.immobile?.indirizzo || 'N/A'}
              </span>
            </div>
            <div className="contratto-scadenza">
              <span className={getScadenzaClass(c.data_fine)}>
                {formatDate(c.data_fine)}
              </span>
            </div>
          </li>
        ))}
      </ul>

      <a href="/contratti?scadenza=true" className="widget-link">
        Vedi tutti →
      </a>
    </div>
  )
}

function getScadenzaClass(dataFine) {
  const giorni = Math.floor((new Date(dataFine) - new Date()) / (1000*60*60*24))
  if (giorni < 30) return 'urgente'
  if (giorni < 60) return 'warning'
  return 'normal'
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('it-IT')
}

export default ContrattiScadenzaWidget
```

---

## 3. Notification Service (Priorità MEDIA)

### Struttura Database

```sql
CREATE TABLE platform_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) DEFAULT 'info',  -- 'info', 'warning', 'error', 'success'
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    link_url VARCHAR(500),
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    read_at TIMESTAMP
);

CREATE INDEX idx_notif_user ON platform_notifications(user_id);
CREATE INDEX idx_notif_read ON platform_notifications(user_id, is_read);
```

### Backend Implementation

```python
# backend/app/core/platform/models/notification.py

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from app.core.database import Base
from datetime import datetime

class Notification(Base):
    """Notifica in-app per utente"""
    __tablename__ = "platform_notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    type = Column(String(50), default='info')  # info, warning, error, success
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    link_url = Column(String(500))

    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime)


# backend/app/core/platform/routes/notifications.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.auth.dependencies import get_current_user
from app.core.auth.models import User
from app.core.platform.models.notification import Notification
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/platform/notifications", tags=["Platform - Notifications"])

class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    message: str
    link_url: str | None
    is_read: bool
    created_at: datetime
    read_at: datetime | None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[NotificationResponse])
def get_my_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ritorna notifiche utente corrente"""

    query = db.query(Notification).filter(Notification.user_id == current_user.id)

    if unread_only:
        query = query.filter(Notification.is_read == False)

    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()

    return notifications


@router.post("/{notification_id}/mark-read")
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marca notifica come letta"""

    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        return {"error": "Notification not found"}, 404

    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.commit()

    return {"status": "marked_read"}


@router.post("/mark-all-read")
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marca tutte le notifiche come lette"""

    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({
        'is_read': True,
        'read_at': datetime.utcnow()
    })
    db.commit()

    return {"status": "all_marked_read"}


# Helper per creare notifiche (usabile da moduli)
def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    type: str = 'info',
    link_url: str = None
):
    """
    Crea notifica per utente

    Usabile da moduli:
        from app.core.platform.routes.notifications import create_notification

        create_notification(
            db=db,
            user_id=123,
            title="Contratto in scadenza",
            message="Il contratto ABC scade tra 30 giorni",
            type="warning",
            link_url="/contratti/123"
        )
    """
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        link_url=link_url
    )
    db.add(notification)
    db.commit()
    return notification
```

### Frontend Notification Bell

```javascript
// frontend/src/components/Layout/NotificationBell.jsx

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './NotificationBell.css'

function NotificationBell() {
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    loadNotifications()

    // Poll ogni 30 secondi
    const interval = setInterval(loadNotifications, 30000)
    return () => clearInterval(interval)
  }, [])

  async function loadNotifications() {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(
        'http://localhost:8000/api/v1/platform/notifications/',
        {
          params: { limit: 10 },
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )
      setNotifications(response.data)
      setUnreadCount(response.data.filter(n => !n.is_read).length)
    } catch (error) {
      console.error('Failed to load notifications:', error)
    }
  }

  async function markAsRead(notificationId) {
    try {
      const token = localStorage.getItem('access_token')
      await axios.post(
        `http://localhost:8000/api/v1/platform/notifications/${notificationId}/mark-read`,
        {},
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )
      loadNotifications()
    } catch (error) {
      console.error('Failed to mark as read:', error)
    }
  }

  async function markAllAsRead() {
    try {
      const token = localStorage.getItem('access_token')
      await axios.post(
        'http://localhost:8000/api/v1/platform/notifications/mark-all-read',
        {},
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )
      loadNotifications()
    } catch (error) {
      console.error('Failed to mark all as read:', error)
    }
  }

  return (
    <div className="notification-bell">
      <button
        className="bell-button"
        onClick={() => setIsOpen(!isOpen)}
      >
        <i className="icon-bell"></i>
        {unreadCount > 0 && (
          <span className="badge">{unreadCount}</span>
        )}
      </button>

      {isOpen && (
        <div className="notification-dropdown">
          <div className="dropdown-header">
            <h3>Notifiche</h3>
            {unreadCount > 0 && (
              <button onClick={markAllAsRead} className="mark-all-btn">
                Segna tutte come lette
              </button>
            )}
          </div>

          <div className="notifications-list">
            {notifications.length === 0 ? (
              <div className="no-notifications">
                Nessuna notifica
              </div>
            ) : (
              notifications.map(notif => (
                <div
                  key={notif.id}
                  className={`notification-item ${notif.is_read ? 'read' : 'unread'}`}
                  onClick={() => !notif.is_read && markAsRead(notif.id)}
                >
                  <div className={`notif-icon ${notif.type}`}>
                    <i className={`icon-${getIcon(notif.type)}`}></i>
                  </div>
                  <div className="notif-content">
                    <h4>{notif.title}</h4>
                    <p>{notif.message}</p>
                    <span className="notif-time">
                      {formatTimeAgo(notif.created_at)}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="dropdown-footer">
            <a href="/notifications">Vedi tutte</a>
          </div>
        </div>
      )}
    </div>
  )
}

function getIcon(type) {
  const icons = {
    'info': 'info-circle',
    'warning': 'exclamation-triangle',
    'error': 'times-circle',
    'success': 'check-circle'
  }
  return icons[type] || 'bell'
}

function formatTimeAgo(dateStr) {
  const seconds = Math.floor((new Date() - new Date(dateStr)) / 1000)

  if (seconds < 60) return 'Adesso'
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min fa`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} ore fa`
  return `${Math.floor(seconds / 86400)} giorni fa`
}

export default NotificationBell
```

---

## 4. Registra routers nella Platform

```python
# backend/app/main.py (aggiungere)

# Import platform routes
from app.core.platform.routes import menu, dashboard, notifications

# Registra platform routers
app.include_router(menu.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)
```

---

## Timeline Implementazione

| Settimana | Task | Team | Ore stimate |
|-----------|------|------|-------------|
| **Settimana 1** | Menu Dinamico Backend + Frontend | Platform | 16h |
| | Registrazione menu modulo Affitti | Moduli | 4h |
| **Settimana 2** | Dashboard Backend + Frontend | Platform | 20h |
| | Widget Contratti Scadenza | Moduli | 8h |
| **Settimana 3** | Notification System | Platform | 16h |
| | Integrazione notifiche in Affitti | Moduli | 4h |
| **Settimana 4** | Testing e2e, bug fix, docs | Tutti | 16h |

**TOTALE: 3-4 settimane**

---

## Note Implementazione

### Separazione Platform vs Moduli

```
backend/
├── app/
│   ├── core/
│   │   ├── platform/           # ← NUOVO! Platform features
│   │   │   ├── models/
│   │   │   │   ├── menu.py
│   │   │   │   ├── dashboard.py
│   │   │   │   └── notification.py
│   │   │   └── routes/
│   │   │       ├── menu.py
│   │   │       ├── dashboard.py
│   │   │       └── notifications.py
│   │   ├── auth/               # Auth system esistente
│   │   ├── database.py
│   │   └── ...
│   │
│   └── modules/
│       └── affitti_lungo/      # Moduli business
│           ├── __init__.py     # Registra menu/widget
│           ├── models/
│           ├── routes/
│           └── widgets/        # ← NUOVO! Widget definitions
```

### No Over-Engineering

✅ **SI:**
- FastAPI per tutto
- Database relazionale normale (no event sourcing)
- Polling per notifiche (no WebSocket per MVP)
- Widget hardcoded in frontend (no dynamic loading per MVP)

❌ **NO:**
- RabbitMQ / Celery (per ora)
- Microservizi separati
- Module Federation (per MVP)
- Event bus complesso
