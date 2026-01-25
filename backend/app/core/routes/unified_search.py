"""
Unified Search API Routes

Platform-level API for cross-module entity search.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.platform_services.unified_search import UnifiedSearchService

router = APIRouter(prefix="/search", tags=["Search"])


class SearchResultItem(BaseModel):
    """Single search result item."""
    id: int
    title: str
    subtitle: Optional[str] = None
    url: str
    type: str
    module: str


class EntityResults(BaseModel):
    """Results for a single entity type."""
    module_name: str
    entity_name: str
    display_name: str
    display_name_plural: str
    icon: str
    color: str
    items: List[SearchResultItem]
    count: int


class UnifiedSearchResponse(BaseModel):
    """Response from unified search."""
    results: dict  # Dict[str, EntityResults]
    total: int
    query: str


class SearchableEntityInfo(BaseModel):
    """Info about a searchable entity."""
    module_name: str
    entity_name: str
    display_name: str
    display_name_plural: str
    icon: str
    color: str
    search_fields: List[str]


@router.get("/unified", response_model=UnifiedSearchResponse)
def unified_search(
    q: str = Query(..., min_length=2, max_length=100, description="Search query"),
    modules: Optional[str] = Query(None, description="Comma-separated module names to search"),
    entities: Optional[str] = Query(None, description="Comma-separated entity names to search"),
    limit_per_entity: int = Query(5, ge=1, le=10, description="Max results per entity type"),
    limit: int = Query(20, ge=1, le=50, description="Max total results"),
    db: Session = Depends(get_db),
):
    """
    Execute unified search across all registered entities.

    This endpoint searches across all modules that have registered searchable entities.
    Results are grouped by entity type for easy display.

    **Query Parameters:**
    - `q`: Search query (min 2 characters)
    - `modules`: Optional comma-separated list of module names to restrict search
    - `entities`: Optional comma-separated list of entity names to restrict search
    - `limit_per_entity`: Max results per entity type (default 5)
    - `limit`: Max total results (default 20)

    **Example:**
    ```
    GET /api/v1/search/unified?q=mario
    GET /api/v1/search/unified?q=roma&modules=immobili,anagrafica_italiana
    GET /api/v1/search/unified?q=123&entities=Contratto,UnitaImmobiliare
    ```
    """
    service = UnifiedSearchService(db)

    # Parse comma-separated filters
    module_list = [m.strip() for m in modules.split(",")] if modules else None
    entity_list = [e.strip() for e in entities.split(",")] if entities else None

    results = service.search(
        query=q,
        modules=module_list,
        entities=entity_list,
        limit_per_entity=limit_per_entity,
        total_limit=limit,
    )

    return results


@router.get("/entities", response_model=List[SearchableEntityInfo])
def get_searchable_entities(
    db: Session = Depends(get_db),
):
    """
    Get list of all searchable entities.

    Returns information about all entities that are registered for unified search,
    including their module, display name, icon, and searchable fields.

    Useful for building search UI with entity filters.
    """
    service = UnifiedSearchService(db)
    return service.get_searchable_entities()


# ==============================================================================
# Legacy endpoint for backward compatibility
# ==============================================================================

class LegacySearchResult(BaseModel):
    """Legacy search result format for backward compatibility."""
    id: int
    type: str
    title: str
    subtitle: Optional[str] = None
    url: str


class LegacySearchResponse(BaseModel):
    """Legacy search response format."""
    results: List[LegacySearchResult]
    total: int


@router.get("/", response_model=LegacySearchResponse)
def legacy_search(
    q: str = Query(..., min_length=2, max_length=100, description="Search query"),
    limit: int = Query(10, ge=1, le=20, description="Max results"),
    db: Session = Depends(get_db),
):
    """
    Legacy search endpoint for backward compatibility.

    Returns flat list of results (not grouped by entity type).
    Use /search/unified for the new grouped format.
    """
    service = UnifiedSearchService(db)

    unified_results = service.search(
        query=q,
        limit_per_entity=limit,
        total_limit=limit,
    )

    # Flatten results to legacy format
    flat_results = []
    for entity_key, entity_data in unified_results.get("results", {}).items():
        for item in entity_data.get("items", []):
            flat_results.append(LegacySearchResult(
                id=item["id"],
                type=item["type"],
                title=item["title"],
                subtitle=item.get("subtitle"),
                url=item["url"],
            ))

    # Sort by relevance (for now just alphabetically by title)
    flat_results.sort(key=lambda x: x.title.lower())

    # Apply total limit
    flat_results = flat_results[:limit]

    return LegacySearchResponse(
        results=flat_results,
        total=len(flat_results),
    )
