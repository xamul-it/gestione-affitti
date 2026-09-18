"""
Platform Services - Core reusable services for all modules.

This package provides the abstraction layer between modules and the database.
Modules should use these services instead of direct database access to ensure:
- Consistency across modules
- Proper isolation
- Reusable functionality
- Easier testing and maintenance

Available Services:
-------------------

1. EntityService
   Base class for CRUD operations on any entity.
   Usage:
       from app.core.platform_services import EntityService
       service = EntityService(db, MyModel)
       items = service.get_all()

2. SearchService
   Unified search and filtering across entities.
   Usage:
       from app.core.platform_services import SearchService
       search = SearchService(db)
       results = search.search(MyModel, search_term="test", filters={"status": "active"})

3. ImportExportService
   Data import/export in CSV and Excel formats.
   Usage:
       from app.core.platform_services import ImportExportService
       ie = ImportExportService(db)
       csv_data = ie.export_to_csv(MyModel, fields=["field1", "field2"])

Module Development Guidelines:
------------------------------

When developing a module:
1. Import services from this package
2. Don't access database directly (use EntityService)
3. Don't access file_storage directly (use DocumentService)
4. Use SearchService for all search/filter operations
5. Use ImportExportService for data import/export

Example Module Pattern:
-----------------------

```python
# In your module's routes file
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.platform_services import EntityService, SearchService

router = APIRouter(prefix="/myentity", tags=["My Entity"])

@router.get("/")
def get_all(db: Session = Depends(get_db)):
    service = EntityService(db, MyModel)
    return service.get_all(skip=0, limit=100)

@router.get("/search")
def search(q: str, db: Session = Depends(get_db)):
    search = SearchService(db)
    return search.search(
        model=MyModel,
        search_term=q,
        search_fields=["name", "description"]
    )
```

This ensures your module is properly isolated and uses the platform layer.
"""

from .entity_service import EntityService
from .search_service import SearchService
from .import_export_service import ImportExportService
from .address_normalizer_service import AddressNormalizerService, AddressParseResult
from .scadenzario_service import ScadenzarioService
from .scadenza_service import ScadenzaService
from .document_parsing_service import DocumentParsingService
from .notification_service import NotificationService

# Note: DocumentService was moved to affitti_lungo.services.document_service
# It's business-specific and not part of the generic platform layer

# Note: ScadenzaService vs ScadenzarioService
# - ScadenzaService: NEW dedicated service for Scadenza model (universal deadline system)
# - ScadenzarioService: OLD service for tracking deadlines on existing entities (e.g., Documento.data_scadenza)

# Note: DocumentParsingService
# - NEW service for async document parsing orchestration (MRZ, OCR, etc.)
# - Handles upload, job tracking, callbacks, and notifications

__all__ = [
    "EntityService",
    "SearchService",
    "ImportExportService",
    "AddressNormalizerService",
    "AddressParseResult",
    "ScadenzarioService",
    "ScadenzaService",
    "DocumentParsingService",
    "NotificationService",
]
