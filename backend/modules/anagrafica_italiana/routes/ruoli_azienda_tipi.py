"""
API endpoints for RuoloAziendaTipo (Company Role Types) - Domain Data Management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.core.database import get_db, get_public_db, get_tenant_schema
from app.core.models.tenant import Tenant
from app.core.auth.dependencies import require_permission
from app.core.auth.models import User

from ..models import RuoloAziendaTipo, RuoloAziendaTipoOverride, RuoloAzienda
from ..schemas.ruolo_azienda_tipo import (
    RuoloAziendaTipoCreate,
    RuoloAziendaTipoUpdate,
    RuoloAziendaTipoResponse,
    RuoloAziendaTipoMerge
)

router = APIRouter(prefix="/anagrafica/domini/ruoli-azienda-tipi", tags=["Domini - Ruoli Azienda"])


@router.get("/", response_model=List[RuoloAziendaTipoResponse])
def get_all_ruoli_tipi(
    skip: int = 0,
    limit: int = 100,
    attivi_solo: bool = False,
    search: str = None,
    current_user: User = Depends(require_permission("soggetto.view")),
    db: Session = Depends(get_public_db),
    tenant_schema: str | None = Depends(get_tenant_schema),
):
    """
    Ottieni tutti i tipi di ruolo azienda

    - **attivi_solo**: Se True, mostra solo ruoli attivi
    - **search**: Filtra per nome (case-insensitive)
    """
    query = db.query(RuoloAziendaTipo)

    tenant = None
    if tenant_schema:
        tenant = db.query(Tenant).filter(Tenant.schema_name == tenant_schema).first()

    if search:
        search_like = f"%{search}%"
        override_ids = []
        if tenant:
            override_ids = [
                r[0]
                for r in db.query(RuoloAziendaTipoOverride.ruolo_tipo_id).filter(
                    RuoloAziendaTipoOverride.tenant_id == tenant.id,
                    RuoloAziendaTipoOverride.is_deleted == False,
                    RuoloAziendaTipoOverride.nome.ilike(search_like),
                ).all()
            ]
        if override_ids:
            query = query.filter(
                RuoloAziendaTipo.nome.ilike(search_like) |
                RuoloAziendaTipo.id.in_(override_ids)
            )
        else:
            query = query.filter(RuoloAziendaTipo.nome.ilike(search_like))

    ruoli = query.order_by(RuoloAziendaTipo.nome).all()

    overrides_by_id = {}
    if tenant and ruoli:
        ruolo_ids = [r.id for r in ruoli]
        overrides = db.query(RuoloAziendaTipoOverride).filter(
            RuoloAziendaTipoOverride.tenant_id == tenant.id,
            RuoloAziendaTipoOverride.ruolo_tipo_id.in_(ruolo_ids),
        ).all()
        overrides_by_id = {o.ruolo_tipo_id: o for o in overrides}

    merged = []
    for ruolo in ruoli:
        override = overrides_by_id.get(ruolo.id)
        if override and override.is_deleted:
            continue
        nome = override.nome if override and override.nome is not None else ruolo.nome
        descrizione = (
            override.descrizione if override and override.descrizione is not None else ruolo.descrizione
        )
        attivo = override.attivo if override and override.attivo is not None else ruolo.attivo

        if attivi_solo and not attivo:
            continue
        if search and search.lower() not in nome.lower():
            continue

        merged.append({
            "id": ruolo.id,
            "nome": nome,
            "descrizione": descrizione,
            "attivo": attivo,
            "created_at": ruolo.created_at,
            "updated_at": ruolo.updated_at,
        })

    return merged[skip:skip + limit]


@router.get("/{ruolo_tipo_id}", response_model=RuoloAziendaTipoResponse)
def get_ruolo_tipo(
    ruolo_tipo_id: int,
    current_user: User = Depends(require_permission("soggetto.view")),
    db: Session = Depends(get_public_db),
    tenant_schema: str | None = Depends(get_tenant_schema),
):
    """Ottieni un tipo di ruolo specifico"""
    ruolo_tipo = db.query(RuoloAziendaTipo).filter(RuoloAziendaTipo.id == ruolo_tipo_id).first()

    if not ruolo_tipo:
        raise HTTPException(status_code=404, detail="Tipo di ruolo non trovato")

    tenant = None
    if tenant_schema:
        tenant = db.query(Tenant).filter(Tenant.schema_name == tenant_schema).first()

    override = None
    if tenant:
        override = db.query(RuoloAziendaTipoOverride).filter(
            RuoloAziendaTipoOverride.tenant_id == tenant.id,
            RuoloAziendaTipoOverride.ruolo_tipo_id == ruolo_tipo_id,
        ).first()
        if override and override.is_deleted:
            raise HTTPException(status_code=404, detail="Tipo di ruolo non trovato")

    return {
        "id": ruolo_tipo.id,
        "nome": (override.nome if override and override.nome is not None else ruolo_tipo.nome),
        "descrizione": (override.descrizione if override and override.descrizione is not None else ruolo_tipo.descrizione),
        "attivo": (override.attivo if override and override.attivo is not None else ruolo_tipo.attivo),
        "created_at": ruolo_tipo.created_at,
        "updated_at": ruolo_tipo.updated_at,
    }


@router.post("/", response_model=RuoloAziendaTipoResponse, status_code=status.HTTP_201_CREATED)
def create_ruolo_tipo(
    ruolo_data: RuoloAziendaTipoCreate,
    current_user: User = Depends(require_permission("soggetto.create")),
    db: Session = Depends(get_db)
):
    """
    Crea un nuovo tipo di ruolo

    - Il nome deve essere univoco (case-insensitive per evitare duplicati)
    """
    # Verifica duplicati (case-insensitive)
    existing = db.query(RuoloAziendaTipo).filter(
        func.lower(RuoloAziendaTipo.nome) == func.lower(ruolo_data.nome)
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Esiste già un ruolo con nome '{existing.nome}'"
        )

    ruolo_tipo = RuoloAziendaTipo(**ruolo_data.model_dump())
    db.add(ruolo_tipo)
    db.commit()
    db.refresh(ruolo_tipo)

    return ruolo_tipo


@router.put("/{ruolo_tipo_id}", response_model=RuoloAziendaTipoResponse)
def update_ruolo_tipo(
    ruolo_tipo_id: int,
    ruolo_update: RuoloAziendaTipoUpdate,
    current_user: User = Depends(require_permission("soggetto.update")),
    db: Session = Depends(get_db)
):
    """Aggiorna un tipo di ruolo esistente"""
    ruolo_tipo = db.query(RuoloAziendaTipo).filter(RuoloAziendaTipo.id == ruolo_tipo_id).first()

    if not ruolo_tipo:
        raise HTTPException(status_code=404, detail="Tipo di ruolo non trovato")

    # Se si sta cambiando il nome, verifica duplicati
    if ruolo_update.nome and ruolo_update.nome != ruolo_tipo.nome:
        existing = db.query(RuoloAziendaTipo).filter(
            func.lower(RuoloAziendaTipo.nome) == func.lower(ruolo_update.nome),
            RuoloAziendaTipo.id != ruolo_tipo_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Esiste già un ruolo con nome '{existing.nome}'"
            )

    # Aggiorna i campi
    update_data = ruolo_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ruolo_tipo, field, value)

    db.commit()
    db.refresh(ruolo_tipo)

    return ruolo_tipo


@router.delete("/{ruolo_tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ruolo_tipo(
    ruolo_tipo_id: int,
    current_user: User = Depends(require_permission("soggetto.delete")),
    db: Session = Depends(get_db)
):
    """
    Elimina un tipo di ruolo

    ATTENZIONE: Non è possibile eliminare un ruolo se è utilizzato in associazioni esistenti.
    Usare la funzione di merge per unificare ruoli simili prima di eliminare.
    """
    ruolo_tipo = db.query(RuoloAziendaTipo).filter(RuoloAziendaTipo.id == ruolo_tipo_id).first()

    if not ruolo_tipo:
        raise HTTPException(status_code=404, detail="Tipo di ruolo non trovato")

    # Verifica se è utilizzato
    usage_count = db.query(RuoloAzienda).filter(RuoloAzienda.ruolo_tipo_id == ruolo_tipo_id).count()

    if usage_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Impossibile eliminare: il ruolo è utilizzato in {usage_count} associazione/i. "
                   f"Usa la funzione di merge per unificare con un altro ruolo prima di eliminare."
        )

    db.delete(ruolo_tipo)
    db.commit()

    return None


@router.post("/merge", response_model=dict, status_code=status.HTTP_200_OK)
def merge_ruoli_tipi(
    merge_data: RuoloAziendaTipoMerge,
    current_user: User = Depends(require_permission("soggetto.update")),
    db: Session = Depends(get_db)
):
    """
    Unifica due tipi di ruolo (merge)

    Tutte le associazioni che usano il ruolo source_id verranno spostate su target_id,
    poi il ruolo source_id verrà eliminato.

    Esempio: Unificare "segretaria" (source_id=2) in "Segretaria" (target_id=1)
    """
    if merge_data.source_id == merge_data.target_id:
        raise HTTPException(status_code=400, detail="Source e target devono essere diversi")

    # Verifica esistenza
    source = db.query(RuoloAziendaTipo).filter(RuoloAziendaTipo.id == merge_data.source_id).first()
    target = db.query(RuoloAziendaTipo).filter(RuoloAziendaTipo.id == merge_data.target_id).first()

    if not source:
        raise HTTPException(status_code=404, detail=f"Ruolo source (ID {merge_data.source_id}) non trovato")
    if not target:
        raise HTTPException(status_code=404, detail=f"Ruolo target (ID {merge_data.target_id}) non trovato")

    # Sposta tutte le associazioni da source a target
    associazioni = db.query(RuoloAzienda).filter(RuoloAzienda.ruolo_tipo_id == merge_data.source_id).all()
    updated_count = len(associazioni)

    for associazione in associazioni:
        associazione.ruolo_tipo_id = merge_data.target_id
        # Azzera il campo ruolo text (ora usa ruolo_tipo)
        associazione.ruolo = None

    # Elimina il ruolo source
    db.delete(source)
    db.commit()

    return {
        "message": f"Merge completato con successo",
        "source_nome": source.nome,
        "target_nome": target.nome,
        "associazioni_aggiornate": updated_count
    }
