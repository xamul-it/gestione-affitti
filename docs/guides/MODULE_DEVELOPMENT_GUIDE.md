# Gestione Affitti - Module Development Guide

**Version:** 1.0.0
**Last Updated:** 2025-11-28
**Target Audience:** Module Developers

---

## Table of Contents

1. [Introduction](#introduction)
2. [Module System Overview](#module-system-overview)
3. [Getting Started](#getting-started)
4. [Module Structure](#module-structure)
5. [Manifest Specification](#manifest-specification)
6. [Backend Development](#backend-development)
7. [Frontend Development](#frontend-development)
8. [Platform Services](#platform-services)
9. [Dependencies](#dependencies)
10. [Testing Modules](#testing-modules)
11. [Publishing Modules](#publishing-modules)
12. [Best Practices](#best-practices)
13. [Examples](#examples)

---

## Introduction

The Gestione Affitti module system allows developers to extend the application with custom functionality without modifying the core codebase. Modules are self-contained packages that can provide:

- Backend API endpoints
- Frontend UI components
- Database models
- Business logic
- Integration with external services

### Why Modules?

- **Extensibility:** Add features without core modifications
- **Maintainability:** Isolated code = easier updates
- **Reusability:** Share modules across installations
- **Multi-team Development:** Teams work independently
- **Customer Customization:** Enable/disable features per customer

---

## Module System Overview

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Module System                         │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐        ┌──────────────┐               │
│  │   Module     │        │   Module     │               │
│  │  Discovery   │───────▶│  Registry    │               │
│  │   & Loader   │        │  (Database)  │               │
│  └──────────────┘        └──────────────┘               │
│         │                        │                        │
│         ▼                        ▼                        │
│  ┌──────────────┐        ┌──────────────┐               │
│  │ Dependency   │        │   Module     │               │
│  │  Resolution  │        │   Backend    │               │
│  └──────────────┘        └──────┬───────┘               │
│         │                        │                        │
│         │                        ▼                        │
│         │                ┌──────────────┐                │
│         │                │  Platform    │                │
│         └───────────────▶│  Services    │                │
│                          └──────────────┘                │
│                                 │                         │
│                                 ▼                         │
│                          ┌──────────────┐                │
│                          │   Database   │                │
│                          └──────────────┘                │
│                                                           │
└─────────────────────────────────────────────────────────┘

        ▲                           ▲
        │                           │
┌───────┴─────────┐         ┌───────┴─────────┐
│  Backend API    │         │  Frontend SPA   │
│  (FastAPI)      │         │  (React)        │
└─────────────────┘         └─────────────────┘
```

### Lifecycle

1. **Discovery:** System scans `modules/` directory at startup
2. **Validation:** Manifest is parsed and validated
3. **Installation:** Module metadata stored in database
4. **Dependency Check:** Dependencies resolved and validated
5. **Loading:** Module code imported and entry point called
6. **Registration:** Routes, hooks, extensions registered
7. **Activation:** Module becomes available to users

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend modules)
- Access to development environment
- Understanding of FastAPI and React

### Development Environment Setup

```bash
# Clone repository
git clone https://github.com/your-org/gestione-affitti.git
cd gestione-affitti

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Start development servers
# Terminal 1: Backend
cd backend && source venv/bin/activate && python app/main.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Create Your First Module

```bash
# Navigate to modules directory
cd backend/modules

# Create module directory
mkdir my_first_module
cd my_first_module

# Create required files
touch __init__.py
touch __manifest__.py
mkdir backend
touch backend/__init__.py
```

---

## Module Structure

### Directory Layout

```
backend/modules/my_module/
├── __init__.py                  # Module package init (required)
├── __manifest__.py              # Module metadata (required)
│
├── backend/                     # Backend code (optional)
│   ├── __init__.py             # Backend entry point with register()
│   ├── routes.py               # API routes
│   ├── models.py               # Database models
│   ├── schemas.py              # Pydantic schemas
│   ├── services.py             # Business logic
│   └── utils.py                # Helper functions
│
├── frontend/                    # Frontend code (optional)
│   ├── ComponentName.jsx       # React components
│   ├── ComponentName.css       # Component styles
│   └── index.js                # Frontend exports
│
├── tests/                       # Tests (recommended)
│   ├── test_backend.py
│   └── test_frontend.js
│
├── docs/                        # Documentation (recommended)
│   ├── README.md
│   └── API.md
│
└── requirements.txt             # Python dependencies (if any)
```

### Minimal Module

```
my_minimal_module/
├── __init__.py                  # Empty or import backend
├── __manifest__.py              # Module metadata
└── backend/
    └── __init__.py              # Contains register() function
```

---

## Manifest Specification

The `__manifest__.py` file contains module metadata and configuration.

### Complete Manifest Example

```python
# backend/modules/my_module/__manifest__.py

{
    # ===== REQUIRED FIELDS =====

    "name": "My Awesome Module",
    "technical_name": "my_module",
    "version": "1.0.0",
    "backend_entry": "backend:register",

    # ===== METADATA =====

    "author": "Your Name / Company",
    "website": "https://www.your-site.com",
    "category": "Rental Management",  # or "Accounting", "Reporting", etc.
    "license": "MIT",  # or "LGPL-3", "Proprietary", etc.
    "price": 0.0,  # 0.0 for free modules
    "currency": "EUR",

    "summary": "One-line description of the module (max 128 chars)",
    "description": """
Detailed description of the module.

Features:
- Feature 1
- Feature 2
- Feature 3

Use cases:
- Use case 1
- Use case 2
    """,

    # ===== COMPATIBILITY =====

    "core_version_min": "1.0.0",
    "core_version_max": "2.0.0",
    "python_version_min": "3.10",

    # ===== DEPENDENCIES =====

    "depends": [
        "base_module:>=1.0.0",           # Required module with version
        "another_module:^1.2.0",         # Semantic versioning
    ],
    "optional_depends": [
        "optional_module:>=1.0.0",       # Optional dependencies
    ],

    # ===== FRONTEND CONFIGURATION =====

    "frontend_config": {
        "enabled": True,
        "entry_point": "@modules/my_module/MyPage",
    },

    "frontend_routes": [
        {
            "path": "/my-module",
            "component": "@modules/my_module/MyPage",
            "title": "My Module",
            "requiresAuth": True,  # Optional
        },
        {
            "path": "/my-module/:id",
            "component": "@modules/my_module/DetailPage",
            "title": "Detail",
        },
    ],

    "menu_items": [
        {
            "label": "My Module",
            "path": "/my-module",
            "icon": "📦",  # Emoji or icon class
            "order": 100,  # Display order (lower = higher in menu)
            "parent": None,  # Parent menu item (for nested menus)
            "permissions": ["my_module.view"],  # Optional
        },
    ],

    "extension_points": [
        {
            "point": "property.detail.tabs",  # Extension point name
            "component": "@modules/my_module/PropertyTab",
            "order": 10,
            "props": {
                "title": "My Custom Tab",
            },
        },
    ],

    # ===== PERMISSIONS =====

    "permissions": [
        {
            "name": "my_module.view",
            "description": "View my module data",
        },
        {
            "name": "my_module.create",
            "description": "Create my module records",
        },
        {
            "name": "my_module.edit",
            "description": "Edit my module records",
        },
        {
            "name": "my_module.delete",
            "description": "Delete my module records",
        },
    ],

    # ===== CONFIGURATION =====

    "installable": True,
    "auto_install": False,  # Auto-install when dependencies met
    "application": False,   # True if standalone application
}
```

### Manifest Field Reference

#### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Human-readable module name |
| `technical_name` | string | Unique identifier (lowercase, underscore) |
| `version` | string | Semantic version (e.g., "1.2.3") |
| `backend_entry` | string | Entry point (format: "module:function") |

#### Optional Metadata

| Field | Type | Description |
|-------|------|-------------|
| `author` | string | Author name or company |
| `website` | string | Module website URL |
| `category` | string | Module category |
| `license` | string | Software license |
| `price` | float | Module price (0.0 for free) |
| `summary` | string | Short description (max 128 chars) |
| `description` | string | Detailed description (markdown) |

#### Dependencies

| Field | Type | Description |
|-------|------|-------------|
| `depends` | list[string] | Required dependencies |
| `optional_depends` | list[string] | Optional dependencies |

**Version Constraint Operators:**
- `>=1.0.0` - Greater than or equal
- `^1.2.0` - Compatible (1.2.0 to <2.0.0)
- `~1.2.3` - Patch-level (~1.2.3 = >=1.2.3, <1.3.0)
- `==1.0.0` - Exact version
- `!=1.0.0` - Not this version
- `<2.0.0` - Less than
- `>1.0.0` - Greater than

---

## Backend Development

### Entry Point

Every module must have a `register()` function in its backend entry point.

```python
# backend/modules/my_module/backend/__init__.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.platform_services import EntityService, SearchService

# Create router
router = APIRouter(prefix="/my-module", tags=["My Module"])


@router.get("/")
async def hello():
    """Example endpoint."""
    return {"message": "Hello from My Module!"}


@router.get("/data")
async def get_data(db: Session = Depends(get_db)):
    """Example endpoint using Platform Services."""
    # Use EntityService to interact with database
    service = EntityService(db, YourModel)
    data = service.get_all(limit=10)
    return data


def register(registry):
    """
    Module entry point - called by module loader.

    Args:
        registry: ModuleRegistry instance

    This function is called when the module is loaded.
    Use it to register routes, hooks, and other resources.
    """
    print(f"[My Module] Registering...")

    # Register router
    registry.register_router("my_module", router)

    # Register hooks (optional)
    # registry.register_hook("my_module", "before_create_property", my_hook_function)

    # Register extension points (optional)
    # registry.register_extension("my_module", "property.detail", MyExtensionComponent)

    print(f"[My Module] Registration complete!")
```

### Database Models

**Use Platform Services instead of direct models when possible.** If you need custom models:

```python
# backend/modules/my_module/backend/models.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class MyCustomModel(Base):
    """Custom database model for my module."""

    __tablename__ = "my_module_custom"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String)
    value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Foreign key to core model (if needed)
    unita_immobiliare_id = Column(Integer, ForeignKey("unita_immobiliari.id"))
    unita_immobiliare = relationship("UnitaImmobiliare")

    def __repr__(self):
        return f"<MyCustomModel(id={self.id}, name='{self.name}')>"
```

**Important:** Create tables in a migration or during module installation:

```python
# In register() function:
def register(registry):
    from app.core.database import engine
    from .models import MyCustomModel

    # Create tables
    MyCustomModel.__table__.create(bind=engine, checkfirst=True)

    # Register router
    registry.register_router("my_module", router)
```

### Pydantic Schemas

```python
# backend/modules/my_module/backend/schemas.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class MyModelBase(BaseModel):
    """Base schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    value: Optional[float] = None

    @field_validator('value')
    @classmethod
    def validate_value(cls, v):
        if v is not None and v < 0:
            raise ValueError('Value must be non-negative')
        return v


class MyModelCreate(MyModelBase):
    """Schema for creating records."""
    unita_immobiliare_id: Optional[int] = None


class MyModelUpdate(BaseModel):
    """Schema for updating records (all fields optional)."""
    name: Optional[str] = None
    description: Optional[str] = None
    value: Optional[float] = None


class MyModelResponse(MyModelBase):
    """Schema for API responses."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

### API Routes

```python
# backend/modules/my_module/backend/routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.platform_services import EntityService
from .models import MyCustomModel
from .schemas import MyModelCreate, MyModelUpdate, MyModelResponse

router = APIRouter(prefix="/my-module", tags=["My Module"])


@router.get("/items", response_model=List[MyModelResponse])
async def get_items(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all items using Platform Services."""
    service = EntityService(db, MyCustomModel)
    items = service.get_all(skip=skip, limit=limit)
    return items


@router.get("/items/{item_id}", response_model=MyModelResponse)
async def get_item(item_id: int, db: Session = Depends(get_db)):
    """Get item by ID."""
    service = EntityService(db, MyCustomModel)
    item = service.get_or_404(item_id)
    return item


@router.post("/items", response_model=MyModelResponse, status_code=201)
async def create_item(
    item: MyModelCreate,
    db: Session = Depends(get_db)
):
    """Create new item."""
    service = EntityService(db, MyCustomModel)
    new_item = service.create(item)
    return new_item


@router.put("/items/{item_id}", response_model=MyModelResponse)
async def update_item(
    item_id: int,
    item: MyModelUpdate,
    db: Session = Depends(get_db)
):
    """Update existing item."""
    service = EntityService(db, MyCustomModel)
    updated_item = service.update(item_id, item)
    return updated_item


@router.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: int, db: Session = Depends(get_db)):
    """Delete item."""
    service = EntityService(db, MyCustomModel)
    service.delete(item_id)
    return None
```

---

## Frontend Development

### React Component

```jsx
// backend/modules/my_module/frontend/MyPage.jsx

import { useState, useEffect } from 'react';
import './MyPage.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export function MyPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadItems();
  }, []);

  async function loadItems() {
    try {
      const response = await fetch(`${API_BASE_URL}/my-module/items`);
      if (!response.ok) {
        throw new Error('Failed to fetch items');
      }
      const data = await response.json();
      setItems(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    const newItem = {
      name: "New Item",
      description: "Created from frontend",
      value: 100,
    };

    try {
      const response = await fetch(`${API_BASE_URL}/my-module/items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newItem),
      });

      if (!response.ok) {
        throw new Error('Failed to create item');
      }

      // Reload items
      loadItems();
    } catch (err) {
      alert('Error: ' + err.message);
    }
  }

  if (loading) {
    return <div className="my-module-page">Loading...</div>;
  }

  if (error) {
    return <div className="my-module-page error">Error: {error}</div>;
  }

  return (
    <div className="my-module-page">
      <header className="page-header">
        <h1>My Module</h1>
        <button onClick={handleCreate} className="btn-primary">
          Create New Item
        </button>
      </header>

      <div className="items-list">
        {items.length === 0 ? (
          <p>No items found</p>
        ) : (
          <table className="items-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Description</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.name}</td>
                  <td>{item.description || 'N/A'}</td>
                  <td>{item.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default MyPage;
```

### Component Styles

```css
/* backend/modules/my_module/frontend/MyPage.css */

.my-module-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0e0e0;
}

.page-header h1 {
  margin: 0;
  font-size: 2rem;
  color: #333;
}

.btn-primary {
  background-color: #667eea;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background-color: #5568d3;
}

.items-list {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  padding: 20px;
}

.items-table {
  width: 100%;
  border-collapse: collapse;
}

.items-table th {
  text-align: left;
  padding: 12px;
  background-color: #f8f9fa;
  border-bottom: 2px solid #dee2e6;
  font-weight: 600;
  color: #333;
}

.items-table td {
  padding: 12px;
  border-bottom: 1px solid #dee2e6;
}

.items-table tbody tr:hover {
  background-color: #f8f9fa;
}

.error {
  color: #dc3545;
  padding: 20px;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 5px;
}
```

### Registering Frontend Component

After creating your component, copy it to the frontend modules directory:

```bash
# Copy module frontend to main frontend
cp -r backend/modules/my_module/frontend/* \
  frontend/src/modules/my_module/
```

Then register it in `frontend/src/App.jsx`:

```jsx
// Import module component
import MyPage from './modules/my_module/MyPage';
import { registerModuleComponent } from './core/modules/DynamicRoutes';

// Register component
registerModuleComponent('@modules/my_module/MyPage', MyPage);
```

---

## Platform Services

**Always use Platform Services instead of direct database access.** This ensures consistency, maintainability, and future compatibility.

### EntityService

Generic CRUD operations for any model.

```python
from app.core.platform_services import EntityService

# In your route handler:
def my_endpoint(db: Session = Depends(get_db)):
    service = EntityService(db, YourModel)

    # Get all records
    records = service.get_all(skip=0, limit=10)

    # Get by ID (raises 404 if not found)
    record = service.get_or_404(1)

    # Get with filters
    records = service.get_all(filters={"status": "active"})

    # Create
    new_record = service.create(YourCreateSchema(...))

    # Update
    updated = service.update(1, YourUpdateSchema(...))

    # Delete
    service.delete(1)

    # Find one by criteria
    record = service.find_by(name="Something")

    # Find all by criteria
    records = service.find_all_by(status="active")
```

### SearchService

Advanced search with filters, aggregations, and full-text search.

```python
from app.core.platform_services import SearchService

# In your route handler:
def search_endpoint(q: str, db: Session = Depends(get_db)):
    search = SearchService(db)

    # Full-text search
    results, total = search.search(
        model=YourModel,
        search_term=q,
        search_fields=["name", "description"],
        return_count=True
    )

    # Search with filters
    results = search.search(
        model=YourModel,
        search_term=q,
        search_fields=["name"],
        filters={"status": "active", "value__gte": 100},
        order_by=["-created_at"],
        limit=20
    )

    # Aggregations
    stats = search.aggregate(
        model=YourModel,
        aggregations={
            "total_count": ("id", "count"),
            "average_value": ("value", "avg"),
            "total_sum": ("value", "sum"),
        },
        filters={"status": "active"},
        group_by=["category"]
    )

    # Autocomplete
    suggestions = search.autocomplete(
        model=YourModel,
        field="name",
        search_term="tes",
        limit=10
    )
```

**Filter Operators:**
- `field`: Exact match
- `field__eq`: Equal (explicit)
- `field__ne`: Not equal
- `field__gt`: Greater than
- `field__gte`: Greater than or equal
- `field__lt`: Less than
- `field__lte`: Less than or equal
- `field__like`: SQL LIKE (case-sensitive)
- `field__ilike`: SQL ILIKE (case-insensitive)
- `field__in`: IN list
- `field__not_in`: NOT IN list
- `field__is_null`: IS NULL (pass boolean)
- `field__between`: BETWEEN (pass [min, max])

### DocumentService

File upload and management.

```python
from app.core.platform_services import DocumentService
from fastapi import UploadFile

# In your route handler:
async def upload_file(
    file: UploadFile,
    entity_id: int,
    db: Session = Depends(get_db)
):
    doc_service = DocumentService(db)

    # Upload file
    document = await doc_service.upload(
        file=file,
        entity_type="my_module",
        entity_id=entity_id,
        filename=file.filename,
        tipo="document",
        descrizione="Uploaded document"
    )

    return document

# Get file path
def download_file(doc_id: int, db: Session = Depends(get_db)):
    doc_service = DocumentService(db)
    file_path = doc_service.get_file_path(doc_id)
    return FileResponse(file_path)

# Delete file
def delete_file(doc_id: int, db: Session = Depends(get_db)):
    doc_service = DocumentService(db)
    doc_service.delete(doc_id)
```

### ImportExportService

CSV/Excel import and export.

```python
from app.core.platform_services import ImportExportService

# Export to CSV
def export_csv(db: Session = Depends(get_db)):
    service = ImportExportService(db)

    csv_content = service.export_to_csv(
        model=YourModel,
        fields=["id", "name", "value", "created_at"],
        filters={"status": "active"},
        order_by=["name"]
    )

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=export.csv"}
    )

# Import from CSV
async def import_csv(file: UploadFile, db: Session = Depends(get_db)):
    service = ImportExportService(db)

    csv_data = await file.read()
    result = service.import_from_csv(
        model=YourModel,
        csv_data=csv_data.decode('utf-8'),
        field_mapping={
            "Name": "name",
            "Value": "value",
        },
        create_schema=YourCreateSchema,
        validate=True
    )

    return result  # {"imported": 10, "errors": []}
```

---

## Dependencies

### Declaring Dependencies

In your `__manifest__.py`:

```python
{
    "depends": [
        "base_module:>=1.0.0",
        "auth_module:^1.2.0",
    ],
    "optional_depends": [
        "reporting_module:>=2.0.0",
    ],
}
```

### Using Dependency Features

```python
# backend/modules/my_module/backend/__init__.py

def register(registry):
    # Check if optional dependency is available
    if registry.is_module_enabled("reporting_module"):
        # Use reporting features
        from reporting_module import generate_report
        # ... use it
    else:
        # Provide alternative or skip
        pass

    # Access dependency features
    base_service = registry.get_module("base_module").get_service()
```

---

## Testing Modules

### Backend Tests

```python
# backend/modules/my_module/tests/test_backend.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    Base.metadata.drop_all(bind=engine)


def test_get_items(client):
    response = client.get("/api/v1/my-module/items")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_item(client):
    item = {
        "name": "Test Item",
        "description": "Test Description",
        "value": 100.0
    }
    response = client.post("/api/v1/my-module/items", json=item)
    assert response.status_code == 201
    assert response.json()["name"] == "Test Item"


def test_get_item_not_found(client):
    response = client.get("/api/v1/my-module/items/999")
    assert response.status_code == 404
```

### Frontend Tests

```javascript
// backend/modules/my_module/tests/test_frontend.js

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MyPage } from '../frontend/MyPage';

// Mock fetch
global.fetch = jest.fn();

describe('MyPage', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('renders loading state', () => {
    fetch.mockImplementation(() => new Promise(() => {}));
    render(<MyPage />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  test('renders items after loading', async () => {
    const mockItems = [
      { id: 1, name: 'Item 1', description: 'Desc 1', value: 100 },
      { id: 2, name: 'Item 2', description: 'Desc 2', value: 200 },
    ];

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockItems,
    });

    render(<MyPage />);

    await waitFor(() => {
      expect(screen.getByText('Item 1')).toBeInTheDocument();
      expect(screen.getByText('Item 2')).toBeInTheDocument();
    });
  });

  test('handles create button click', async () => {
    fetch.mockResolvedValueOnce({ ok: true, json: async () => [] });
    fetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    fetch.mockResolvedValueOnce({ ok: true, json: async () => [] });

    render(<MyPage />);

    const createButton = await screen.findByText('Create New Item');
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/my-module/items'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });
});
```

### Running Tests

```bash
# Backend tests
cd backend
pytest modules/my_module/tests/

# Frontend tests
cd frontend
npm test modules/my_module
```

---

## Publishing Modules

### Module Package Structure

```
my_module/
├── __manifest__.py
├── __init__.py
├── backend/
├── frontend/
├── tests/
├── docs/
├── README.md
├── LICENSE
└── CHANGELOG.md
```

### Versioning

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR:** Breaking changes
- **MINOR:** New features (backward compatible)
- **PATCH:** Bug fixes

### Distribution

1. **Git Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git tag v1.0.0
   git push origin main --tags
   ```

2. **Module Marketplace** (future)
   - Upload to module repository
   - Include screenshots, documentation
   - Pricing information

3. **Private Distribution**
   - Zip module directory
   - Share with customers
   - Installation: extract to `modules/` directory

---

## Best Practices

### Code Quality

1. **Use Platform Services**
   - ✅ Always use EntityService, SearchService
   - ❌ Never use direct `db.query()`

2. **Validation**
   - Use Pydantic validators
   - Validate business rules
   - Return clear error messages

3. **Error Handling**
   ```python
   try:
       result = service.get_or_404(id)
   except HTTPException:
       # Let it propagate (404)
       raise
   except Exception as e:
       # Log and return 500
       logger.error(f"Error: {e}")
       raise HTTPException(status_code=500, detail="Internal error")
   ```

4. **Logging**
   ```python
   import logging
   logger = logging.getLogger(__name__)

   logger.info(f"Processing item {id}")
   logger.warning(f"Unusual value: {value}")
   logger.error(f"Failed to process: {e}")
   ```

### Security

1. **Input Validation**
   - Validate all inputs with Pydantic
   - Sanitize user input
   - Use parameterized queries (automatic with ORM)

2. **Authentication** (future)
   ```python
   from app.core.auth import get_current_user

   @router.get("/items")
   async def get_items(user = Depends(get_current_user)):
       # user authenticated
       pass
   ```

3. **Permissions** (future)
   ```python
   from app.core.auth import require_permission

   @router.delete("/items/{id}")
   async def delete_item(
       id: int,
       user = Depends(require_permission("my_module.delete"))
   ):
       # user has permission
       pass
   ```

### Performance

1. **Database Queries**
   - Use pagination (`skip`, `limit`)
   - Use filters to reduce data
   - Avoid N+1 queries (use joinedload)

2. **Caching** (future)
   ```python
   from app.core.cache import cache

   @cache(ttl=300)  # 5 minutes
   def get_expensive_data():
       # computed once, cached
       pass
   ```

3. **Async Operations**
   - Use `async def` for I/O operations
   - Use `await` for external calls

### Documentation

1. **Docstrings**
   ```python
   def my_function(param1: str, param2: int) -> dict:
       """
       Short description.

       Detailed description explaining the function's purpose,
       behavior, and any important notes.

       Args:
           param1: Description of param1
           param2: Description of param2

       Returns:
           Dictionary containing result data

       Raises:
           ValueError: If param2 is negative
           HTTPException: If resource not found
       """
       pass
   ```

2. **API Documentation**
   - FastAPI auto-generates OpenAPI docs
   - Add descriptions to routes
   - Use response_model

3. **Module README**
   - Installation instructions
   - Configuration
   - Usage examples
   - Troubleshooting

---

## Examples

### Complete Minimal Module

See `backend/modules/hello_module/` for a working example.

### Module with Dependencies

See `backend/modules/advanced_hello/` for a module that depends on `hello_module`.

### Module with Frontend

The hello_module includes a complete frontend example with:
- React component (HelloPage.jsx)
- API integration
- Styling
- Error handling
- Loading states

---

## Support & Resources

### Documentation
- **Platform Services API:** See `backend/app/core/platform_services/`
- **Module System:** See `backend/app/core/module_system/`
- **Example Modules:** See `backend/modules/`

### Community
- **Forum:** https://community.your-domain.com
- **Discord:** https://discord.gg/your-channel
- **Email:** developers@your-company.com

### Contributing
- Report bugs on GitHub Issues
- Submit pull requests
- Share your modules in the marketplace

---

## Appendix

### Module Checklist

- [ ] `__manifest__.py` completed with all required fields
- [ ] Backend entry point with `register()` function
- [ ] API routes use Platform Services
- [ ] Pydantic schemas with validation
- [ ] Frontend component created (if applicable)
- [ ] Frontend routes registered in manifest
- [ ] Tests written and passing
- [ ] Documentation written (README.md)
- [ ] Dependencies declared correctly
- [ ] Version number follows semantic versioning
- [ ] Module tested in development environment
- [ ] No direct database access (`db.query()`)
- [ ] Error handling implemented
- [ ] Logging added for debugging
- [ ] Security considerations addressed

---

**End of Module Development Guide**

**Version:** 1.0.0
**Last Updated:** 2025-11-28
