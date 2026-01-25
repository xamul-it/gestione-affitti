"""
API routes for Anagrafica domain data (Comuni, Tipi Documento).

Provides read-only access to reference data used by the registry module.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from typing import List, Optional
from app.core.database import get_db, get_public_db, get_tenant_schema
from app.core.auth.dependencies import get_current_user, require_permission
from app.core.auth.models import User

# Import from this module
from ..models import (
    ComuneItalia,
    ComuneItaliaOverride,
    TipoDocumento,
    TipoDocumentoOverride,
    StatoDocumento,
    StatoDocumentoOverride,
)
from ..services.comuni_sync_service import sync_comuni_italia

router = APIRouter(prefix="/anagrafica/domini", tags=["anagrafica-domini"])


# ============================================================================
# COMUNI ITALIA
# ============================================================================

@router.get("/comuni", response_model=List[dict])
def list_comuni(
    skip: int = 0,
    limit: int = 100,
    provincia: Optional[str] = Query(None, max_length=2),
    search: Optional[str] = Query(None, max_length=100),
    db: Session = Depends(get_db),
    public_db: Session = Depends(get_public_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(get_current_user)
):
    """
    List Italian municipalities (comuni).

    Query parameters:
    - provincia: Filter by province code (e.g., "MI", "BO")
    - search: Search by municipality name (case-insensitive partial match)
    """
    query = public_db.query(ComuneItalia)

    if provincia:
        query = query.filter(ComuneItalia.provincia_sigla == provincia.upper())

    if search:
        search_normalized = search.lower()
        query = query.filter(ComuneItalia.nome_normalized.contains(search_normalized))

    comuni = query.order_by(ComuneItalia.nome).offset(skip).limit(limit).all()

    overrides_by_comune = {}
    if tenant_schema and comuni:
        try:
            inspector = inspect(db.get_bind())
            if inspector.has_table("anag_comuni_italia_overrides", schema=tenant_schema):
                comune_ids = [c.id for c in comuni]
                overrides = db.query(ComuneItaliaOverride).filter(
                    ComuneItaliaOverride.comune_id.in_(comune_ids),
                ).all()
                overrides_by_comune = {o.comune_id: o for o in overrides}
        except Exception:
            overrides_by_comune = {}

    return [
        {
            "id": c.id,
            "nome": (o.nome if o and o.nome is not None else c.nome),
            "cap": (o.cap if o and o.cap is not None else c.cap),
            "provincia_sigla": (o.provincia_sigla if o and o.provincia_sigla is not None else c.provincia_sigla),
            "provincia_nome": (o.provincia_nome if o and o.provincia_nome is not None else c.provincia_nome),
            "regione": (o.regione if o and o.regione is not None else c.regione),
            "codice_istat": (o.codice_istat if o and o.codice_istat is not None else c.codice_istat),
            "codice_catastale": (o.codice_catastale if o and o.codice_catastale is not None else c.codice_catastale),
            "attivo": (c.attivo if c.attivo is not None else True),
        }
        for c in comuni
        for o in [overrides_by_comune.get(c.id)]
        if not (o and o.is_deleted)
    ]


@router.post("/comuni/refresh", response_model=dict)
def refresh_comuni(
    public_db: Session = Depends(get_public_db),
    current_user: User = Depends(require_permission("platform.admin")),
):
    """
    Refresh comuni list from external source and update public database.
    """
    return sync_comuni_italia(public_db)


@router.get("/comuni/{comune_id}", response_model=dict)
def get_comune(
    comune_id: int,
    db: Session = Depends(get_db),
    public_db: Session = Depends(get_public_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(get_current_user)
):
    """Get a specific comune by ID"""
    comune = public_db.query(ComuneItalia).filter(ComuneItalia.id == comune_id).first()

    if not comune:
        raise HTTPException(status_code=404, detail="Comune non trovato")

    override = None
    if tenant_schema:
        try:
            inspector = inspect(db.get_bind())
            if inspector.has_table("anag_comuni_italia_overrides", schema=tenant_schema):
                override = db.query(ComuneItaliaOverride).filter(
                    ComuneItaliaOverride.comune_id == comune.id,
                ).first()
                if override and override.is_deleted:
                    raise HTTPException(status_code=404, detail="Comune non trovato")
        except Exception:
            override = None

    return {
        "id": comune.id,
        "nome": (override.nome if override and override.nome is not None else comune.nome),
        "cap": (override.cap if override and override.cap is not None else comune.cap),
        "provincia_sigla": (override.provincia_sigla if override and override.provincia_sigla is not None else comune.provincia_sigla),
        "provincia_nome": (override.provincia_nome if override and override.provincia_nome is not None else comune.provincia_nome),
        "regione": (override.regione if override and override.regione is not None else comune.regione),
        "codice_istat": (override.codice_istat if override and override.codice_istat is not None else comune.codice_istat),
        "codice_catastale": (override.codice_catastale if override and override.codice_catastale is not None else comune.codice_catastale),
        "latitudine": float(override.latitudine) if override and override.latitudine is not None else (float(comune.latitudine) if comune.latitudine else None),
        "longitudine": float(override.longitudine) if override and override.longitudine is not None else (float(comune.longitudine) if comune.longitudine else None),
    }


@router.get("/comuni/search/cap/{cap}", response_model=List[dict])
def search_comuni_by_cap(
    cap: str,
    db: Session = Depends(get_db),
    public_db: Session = Depends(get_public_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(get_current_user)
):
    """Search comuni by postal code (CAP)"""
    core_ids_from_overrides = set()
    overrides_by_comune = {}
    if tenant_schema:
        try:
            inspector = inspect(db.get_bind())
            if inspector.has_table("anag_comuni_italia_overrides", schema=tenant_schema):
                overrides = db.query(ComuneItaliaOverride).filter(
                    ComuneItaliaOverride.cap == cap,
                    ComuneItaliaOverride.is_deleted == False,
                ).all()
                overrides_by_comune = {o.comune_id: o for o in overrides}
                core_ids_from_overrides = {o.comune_id for o in overrides if o.comune_id}
        except Exception:
            overrides_by_comune = {}

    comuni_query = public_db.query(ComuneItalia).filter(ComuneItalia.cap == cap)
    if core_ids_from_overrides:
        comuni_query = comuni_query.union(
            public_db.query(ComuneItalia).filter(ComuneItalia.id.in_(core_ids_from_overrides))
        )
    comuni = comuni_query.all()

    if tenant and comuni:
        comune_ids = [c.id for c in comuni if c.id not in overrides_by_comune]
        if comune_ids:
            extra_overrides = db.query(ComuneItaliaOverride).filter(
                ComuneItaliaOverride.tenant_id == tenant.id,
                ComuneItaliaOverride.comune_id.in_(comune_ids),
            ).all()
            for o in extra_overrides:
                overrides_by_comune[o.comune_id] = o

    return [
        {
            "id": c.id,
            "nome": (o.nome if o and o.nome is not None else c.nome),
            "provincia_sigla": (o.provincia_sigla if o and o.provincia_sigla is not None else c.provincia_sigla),
            "cap": (o.cap if o and o.cap is not None else c.cap),
        }
        for c in comuni
        for o in [overrides_by_comune.get(c.id)]
        if not (o and o.is_deleted)
        if (o.cap if o and o.cap is not None else c.cap) == cap
    ]


# ============================================================================
# TIPI DOCUMENTO
# ============================================================================

@router.get("/tipi-documento", response_model=List[dict])
def list_tipi_documento(
    skip: int = 0,
    limit: int = 100,
    categoria: Optional[str] = Query(None, max_length=50),
    attivi_solo: bool = True,
    db: Session = Depends(get_db),
    public_db: Session = Depends(get_public_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(get_current_user)
):
    """
    List document types.

    Query parameters:
    - categoria: Filter by category (identita, fiscale, aziendale, altro)
    - attivi_solo: Show only active document types (default: true)
    """
    query = public_db.query(TipoDocumento)

    if attivi_solo:
        query = query.filter(TipoDocumento.attivo == True)

    if categoria:
        query = query.filter(TipoDocumento.categoria == categoria)

    tipi = query.order_by(TipoDocumento.nome).offset(skip).limit(limit).all()

    overrides_by_id = {}
    if tenant_schema:
        try:
            inspector = inspect(db.get_bind())
            if inspector.has_table("anag_tipi_documento_overrides", schema=tenant_schema):
                overrides = db.query(TipoDocumentoOverride).all()
                overrides_by_id = {o.tipo_documento_id: o for o in overrides}
        except Exception:
            overrides_by_id = {}

    result = []
    for t in tipi:
        o = overrides_by_id.get(t.id)
        if o and o.is_deleted:
            continue
        result.append({
            "id": t.id,
            "codice": o.codice if o and o.codice is not None else t.codice,
            "nome": o.nome if o and o.nome is not None else t.nome,
            "descrizione": o.descrizione if o and o.descrizione is not None else t.descrizione,
            "categoria": o.categoria if o and o.categoria is not None else t.categoria,
            "richiede_scadenza": o.richiede_scadenza if o and o.richiede_scadenza is not None else t.richiede_scadenza,
            "attivo": o.attivo if o and o.attivo is not None else t.attivo,
        })

    return result


@router.get("/tipi-documento/{tipo_id}", response_model=dict)
def get_tipo_documento(
    tipo_id: int,
    db: Session = Depends(get_db),
    public_db: Session = Depends(get_public_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(get_current_user)
):
    """Get a specific document type by ID"""
    tipo = public_db.query(TipoDocumento).filter(TipoDocumento.id == tipo_id).first()

    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo documento non trovato")

    override = None
    if tenant_schema:
        try:
            inspector = inspect(db.get_bind())
            if inspector.has_table("anag_tipi_documento_overrides", schema=tenant_schema):
                override = db.query(TipoDocumentoOverride).filter(
                    TipoDocumentoOverride.tipo_documento_id == tipo_id
                ).first()
        except Exception:
            override = None

    if override and override.is_deleted:
        raise HTTPException(status_code=404, detail="Tipo documento non trovato")

    return {
        "id": tipo.id,
        "codice": override.codice if override and override.codice is not None else tipo.codice,
        "nome": override.nome if override and override.nome is not None else tipo.nome,
        "descrizione": override.descrizione if override and override.descrizione is not None else tipo.descrizione,
        "categoria": override.categoria if override and override.categoria is not None else tipo.categoria,
        "richiede_scadenza": override.richiede_scadenza if override and override.richiede_scadenza is not None else tipo.richiede_scadenza,
        "attivo": override.attivo if override and override.attivo is not None else tipo.attivo,
    }


@router.get("/categorie-documento", response_model=List[dict])
def list_categorie_documento(
    db: Session = Depends(get_db),
    public_db: Session = Depends(get_public_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(get_current_user)
):
    """Get list of document categories with counts"""
    tipi = list_tipi_documento(
        skip=0,
        limit=10000,
        categoria=None,
        attivi_solo=True,
        db=db,
        public_db=public_db,
        tenant_schema=tenant_schema,
        current_user=current_user,
    )

    counts = {}
    for tipo in tipi:
        categoria = tipo.get("categoria") or "non_specificata"
        counts[categoria] = counts.get(categoria, 0) + 1

    return [
        {"categoria": categoria, "count": count}
        for categoria, count in counts.items()
    ]


# ============================================================================
# STATI DOCUMENTO
# ============================================================================

@router.get("/stati-documento", response_model=List[dict])
def list_stati_documento(
    skip: int = 0,
    limit: int = 100,
    attivi_solo: bool = True,
    db: Session = Depends(get_db),
    public_db: Session = Depends(get_public_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(get_current_user)
):
    """
    List document states.
    """
    query = public_db.query(StatoDocumento)
    if attivi_solo:
        query = query.filter(StatoDocumento.attivo == True)

    stati = query.order_by(StatoDocumento.nome).offset(skip).limit(limit).all()

    overrides_by_id = {}
    if tenant_schema:
        try:
            inspector = inspect(db.get_bind())
            if inspector.has_table("anag_stati_documento_overrides", schema=tenant_schema):
                overrides = db.query(StatoDocumentoOverride).all()
                overrides_by_id = {o.stato_documento_id: o for o in overrides}
        except Exception:
            overrides_by_id = {}

    result = []
    for s in stati:
        o = overrides_by_id.get(s.id)
        if o and o.is_deleted:
            continue
        result.append({
            "id": s.id,
            "codice": o.codice if o and o.codice is not None else s.codice,
            "nome": o.nome if o and o.nome is not None else s.nome,
            "descrizione": o.descrizione if o and o.descrizione is not None else s.descrizione,
            "attivo": o.attivo if o and o.attivo is not None else s.attivo,
        })

    return result


@router.get("/stati-documento/{stato_id}", response_model=dict)
def get_stato_documento(
    stato_id: int,
    db: Session = Depends(get_db),
    public_db: Session = Depends(get_public_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(get_current_user)
):
    """Get a specific document state by ID"""
    stato = public_db.query(StatoDocumento).filter(StatoDocumento.id == stato_id).first()

    if not stato:
        raise HTTPException(status_code=404, detail="Stato documento non trovato")

    override = None
    if tenant_schema:
        try:
            inspector = inspect(db.get_bind())
            if inspector.has_table("anag_stati_documento_overrides", schema=tenant_schema):
                override = db.query(StatoDocumentoOverride).filter(
                    StatoDocumentoOverride.stato_documento_id == stato_id
                ).first()
        except Exception:
            override = None

    if override and override.is_deleted:
        raise HTTPException(status_code=404, detail="Stato documento non trovato")

    return {
        "id": stato.id,
        "codice": override.codice if override and override.codice is not None else stato.codice,
        "nome": override.nome if override and override.nome is not None else stato.nome,
        "descrizione": override.descrizione if override and override.descrizione is not None else stato.descrizione,
        "attivo": override.attivo if override and override.attivo is not None else stato.attivo,
    }
