"""
Role relations between soggetti and module objects (spec
docs/superpowers/specs/2026-11-10-relazioni-ruoli-soggetti-design.md).

Reads need soggetto.view; object details are hidden without the type's
permesso_oggetto. Writes (core relations only) need soggetto.edit plus the
".edit" counterpart of the type's permesso_oggetto (e.g. condominio.edit).
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth.dependencies import require_permission
from app.core.auth.models import User
from app.core.database import get_db, get_tenant_schema
from app.core.models import RuoloDisponibile
from app.core.models.tenant import Tenant, TenantModule
from app.core.platform.models import Relazione
from app.core.platform_services import relazioni_query
from app.core.platform_services.relazione_service import RelazioneService
from app.core.schemas.relazioni import (
    RelazioneCoreOut, RelazioneIn, RelazioneOut, RelazioneUpdate, TipoRelazioneOut,
)

router = APIRouter(prefix="/relazioni", tags=["Relazioni"])


def _schema(tenant_schema) -> Optional[str]:
    return tenant_schema if isinstance(tenant_schema, str) else None


def _moduli_attivi(db: Session, tenant_schema: Optional[str]) -> Optional[set]:
    """Enabled modules of the tenant; None when unknown (no filter)."""
    if not tenant_schema:
        return None
    rows = (db.query(TenantModule.module_id)
            .join(Tenant, Tenant.id == TenantModule.tenant_id)
            .filter(Tenant.schema_name == tenant_schema, TenantModule.enabled.is_(True)).all())
    return {r[0] for r in rows} or None


# Relation types written only through their module's API, which applies its
# own rules and permissions (e.g. soggetto.create/delete for business roles).
API_DEDICATE = {"ruolo_azienda": "/anagrafica/ruoli-azienda"}


def _verifica_scrittura(user: User, tipo: RuoloDisponibile) -> None:
    if tipo.codice in API_DEDICATE:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"I '{tipo.nome_display}' si gestiscono da {API_DEDICATE[tipo.codice]}",
        )
    if user.is_superuser or not tipo.permesso_oggetto:
        return
    richiesto = tipo.permesso_oggetto.rsplit(".", 1)[0] + ".edit"
    if richiesto not in user.get_permissions():
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Insufficient permissions. Required: {richiesto}")


def _errori(fn):
    try:
        return fn()
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))


@router.get("/tipi", response_model=List[TipoRelazioneOut])
def list_tipi(
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    tenant_schema=Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.view")),
):
    attivi = _moduli_attivi(db, _schema(tenant_schema))
    out = []
    for t in (db.query(RuoloDisponibile).filter(RuoloDisponibile.attivo.is_(True))
              .order_by(RuoloDisponibile.nome_display).all()):
        if attivi is not None and t.modulo_id not in attivi:
            continue
        if entity_type and entity_type not in (t.entity_types or []):
            continue
        out.append(TipoRelazioneOut(
            id=t.id, codice=t.codice, nome=t.nome_display, modulo=t.modulo_id, fonte=t.fonte,
            entity_types=t.entity_types, scadenza=t.scadenza, unico_per_oggetto=t.unico_per_oggetto,
            sottotipi_fonte=t.sottotipi_fonte,
        ))
    return out


@router.get("/", response_model=List[RelazioneOut])
def list_relazioni(
    soggetto_id: Optional[int] = None,
    tipo: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    solo_correnti: bool = Query(False),
    db: Session = Depends(get_db),
    tenant_schema=Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.view")),
):
    return relazioni_query.elenca(
        db, _schema(tenant_schema), permessi=current_user.get_permissions(),
        soggetto_ids=[soggetto_id] if soggetto_id is not None else None,
        tipo=tipo, entity_type=entity_type, entity_id=entity_id, solo_correnti=solo_correnti,
    )


def _service(db, tenant_schema, user) -> RelazioneService:
    return RelazioneService(db, _schema(tenant_schema), user.id)


@router.post("/", response_model=RelazioneCoreOut, status_code=status.HTTP_201_CREATED)
def create_relazione(
    data: RelazioneIn,
    db: Session = Depends(get_db),
    tenant_schema=Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.edit")),
):
    svc = _service(db, tenant_schema, current_user)
    tipo = _errori(lambda: svc.tipo(data.tipo))
    _verifica_scrittura(current_user, tipo)
    campi = data.model_dump(exclude={"soggetto_id", "tipo"})
    rel = _errori(lambda: svc.crea(data.soggetto_id, data.tipo, **campi))
    db.commit()
    db.refresh(rel)
    return rel


def _tipo_di(db: Session, relazione_id: int) -> RuoloDisponibile:
    rel = db.get(Relazione, relazione_id)
    if rel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Relazione {relazione_id} inesistente")
    return db.get(RuoloDisponibile, rel.ruolo_id)


@router.put("/{relazione_id}", response_model=RelazioneCoreOut)
def update_relazione(
    relazione_id: int,
    data: RelazioneUpdate,
    db: Session = Depends(get_db),
    tenant_schema=Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.edit")),
):
    _verifica_scrittura(current_user, _tipo_di(db, relazione_id))
    svc = _service(db, tenant_schema, current_user)
    rel = _errori(lambda: svc.aggiorna(relazione_id, **data.model_dump(exclude_unset=True)))
    db.commit()
    db.refresh(rel)
    return rel


@router.post("/{relazione_id}/rinnova", response_model=RelazioneCoreOut)
def rinnova_relazione(
    relazione_id: int,
    db: Session = Depends(get_db),
    tenant_schema=Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.edit")),
):
    _verifica_scrittura(current_user, _tipo_di(db, relazione_id))
    rel = _errori(lambda: _service(db, tenant_schema, current_user).rinnova(relazione_id))
    db.commit()
    db.refresh(rel)
    return rel


@router.delete("/{relazione_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_relazione(
    relazione_id: int,
    db: Session = Depends(get_db),
    tenant_schema=Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.edit")),
):
    _verifica_scrittura(current_user, _tipo_di(db, relazione_id))
    _errori(lambda: _service(db, tenant_schema, current_user).elimina(relazione_id))
    db.commit()
    return None
