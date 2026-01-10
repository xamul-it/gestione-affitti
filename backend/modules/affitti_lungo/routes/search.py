from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from typing import List
from app.core.database import get_db
from app.core.platform_services import SearchService
from ..models import UnitaImmobiliare, Affittuario, Contratto
from pydantic import BaseModel
import re

router = APIRouter(prefix="/search", tags=["search"])


def sanitize_search_query(query: str) -> str:
    """
    Sanitize search query to prevent SQL LIKE injection.
    Escapes wildcards and limits special characters.
    """
    # Escape SQL LIKE wildcards
    query = query.replace('\\', '\\\\')  # Escape backslashes first
    query = query.replace('%', r'\%')    # Escape percent
    query = query.replace('_', r'\_')    # Escape underscore

    # Remove potentially dangerous characters
    query = re.sub(r'[^\w\s\-.,àèéìòù]', '', query, flags=re.UNICODE)

    return query.strip()


class SearchResultItem(BaseModel):
    id: int
    type: str  # "immobile", "affittuario", "contratto"
    title: str
    subtitle: str
    url: str

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    results: List[SearchResultItem]
    total: int


@router.get("/", response_model=SearchResponse)
def global_search(
    q: str = Query(..., min_length=2, max_length=100, description="Search query"),
    limit: int = Query(10, le=20, description="Max results per type"),
    db: Session = Depends(get_db)
):
    """
    Global search across immobili, affittuari, and contratti using Platform Services.
    Returns up to 'limit' results for each entity type.

    Refactored to use SearchService for consistent search behavior.
    """
    results = []

    # Sanitize input to prevent SQL injection
    q_safe = sanitize_search_query(q)

    if len(q_safe) < 2:
        return SearchResponse(results=[], total=0)

    # Use SearchService for unified search
    search_service = SearchService(db)

    # Search Unità Immobiliari using SearchService
    unita_immobiliari = search_service.search(
        model=UnitaImmobiliare,
        search_term=q_safe,
        search_fields=["indirizzo", "citta", "cap"],
        order_by=["-created_at"],
        limit=limit
    )

    for unita in unita_immobiliari:
        results.append(SearchResultItem(
            id=unita.id,
            type="unita_immobiliare",
            title=unita.indirizzo,
            subtitle=f"{unita.citta} ({unita.cap}) - {unita.tipo or 'N/A'}",
            url=f"/unita-immobiliari/{unita.id}"
        ))

    # Search Affittuari using SearchService
    affittuari = search_service.search(
        model=Affittuario,
        search_term=q_safe,
        search_fields=["nome", "cognome", "email", "telefono"],
        order_by=["cognome", "nome"],
        limit=limit
    )

    for affittuario in affittuari:
        results.append(SearchResultItem(
            id=affittuario.id,
            type="affittuario",
            title=f"{affittuario.nome} {affittuario.cognome}",
            subtitle=affittuario.email or affittuario.telefono or "N/A",
            url=f"/affittuari/{affittuario.id}"
        ))

    # Search Contratti using SearchService
    # Note: For related data, we still use raw query with joinedload for now
    # A future enhancement would be to add join support to SearchService
    contratti_query = db.query(Contratto).options(
        joinedload(Contratto.unita_immobiliare),
        joinedload(Contratto.affittuario)
    ).filter(
        or_(
            func.lower(Contratto.numero_contratto).contains(q_safe.lower())
        )
    ).order_by(
        Contratto.data_inizio.desc()
    ).limit(limit)

    for contratto in contratti_query:
        unita = contratto.unita_immobiliare
        affittuario = contratto.affittuario

        title = f"Contratto {contratto.numero_contratto}"
        subtitle_parts = []
        if unita:
            subtitle_parts.append(unita.indirizzo)
        if affittuario:
            subtitle_parts.append(f"{affittuario.nome} {affittuario.cognome}")

        results.append(SearchResultItem(
            id=contratto.id,
            type="contratto",
            title=title,
            subtitle=" - ".join(subtitle_parts) if subtitle_parts else "N/A",
            url=f"/contratti/{contratto.id}"
        ))

    return SearchResponse(
        results=results,
        total=len(results)
    )
