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
from app.core.platform_services.relazioni_moduli import moduli_attivi
from app.core.auth.models import User
from app.core.database import get_db, get_tenant_schema
from app.core.models import RuoloDisponibile
from app.core.models.tenant import Tenant, TenantModule
from app.core.platform.models import Relazione
from app.core.platform_services import object_permissions, relazioni_query
from app.core.platform_services.quote import parse_quota
from app.core.platform_services.relazione_service import RelazioneService
from app.core.schemas.relazioni import (
    RelazioneCoreOut, RelazioneIn, RelazioneOut, RelazioneUpdate, TipoRelazioneOut,
)

router = APIRouter(prefix="/relazioni", tags=["Relazioni"])


def _schema(tenant_schema) -> Optional[str]:
    return tenant_schema if isinstance(tenant_schema, str) else None


_moduli_attivi = moduli_attivi


# Relation types written only through their module's API, which applies its
# own rules and permissions (e.g. soggetto.create/delete for business roles).
API_DEDICATE = {"ruolo_azienda": "/anagrafica/ruoli-azienda"}


def _verifica_scrittura(user: User, tipo: RuoloDisponibile, db: Optional[Session] = None, tenant_schema=None,
                        entity_type: Optional[str] = None, entity_id: Optional[int] = None) -> None:
    """Writing needs the ".edit" counterpart of the object's view permission: the module hook's one
    for that object (e.g. terreno.edit for a land parcel) or, without hook, the type's permesso_oggetto."""
    if tipo.codice in API_DEDICATE:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"I '{tipo.nome_display}' si gestiscono da {API_DEDICATE[tipo.codice]}",
        )
    if user.is_superuser:
        return
    permessi = user.get_permissions()
    per_oggetto = (object_permissions.permessi_modifica(db, _schema(tenant_schema), entity_type=entity_type,
                                                        entity_id=entity_id) if db is not None else None)
    richiesti = (object_permissions.permessi_modifica_richiesti(db, _schema(tenant_schema), entity_type=entity_type,
                                                                entity_id=entity_id) if db is not None else None)
    if richiesti and not richiesti <= permessi:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Non hai accesso a questo oggetto")
    if per_oggetto is not None:
        if not per_oggetto & permessi:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Non hai accesso a questo oggetto")
        return
    if not tipo.permesso_oggetto:
        return
    richiesto = tipo.permesso_oggetto.rsplit(".", 1)[0] + ".edit"
    if richiesto not in permessi:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Insufficient permissions. Required: {richiesto}")


def _errori(fn):
    try:
        return fn()
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))


def _verifica_oggetto(db, tenant_schema, user: User, tipo: RuoloDisponibile, entity_type, entity_id,
                      lettura: bool = False) -> None:
    """The caller must be allowed to see the object: the module hook decides if there is one; else,
    reading needs the type's permesso_oggetto (writes are covered by _verifica_scrittura)."""
    if not object_permissions.oggetto_visibile(
        db, _schema(tenant_schema), user.get_permissions(), entity_type=entity_type,
        entity_id=entity_id, permesso_oggetto=tipo.permesso_oggetto if lettura else None,
    ):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Non hai accesso a questo oggetto")


@router.get("/tipi", response_model=List[TipoRelazioneOut])
def list_tipi(
    entity_type: Optional[str] = None,
    famiglia: Optional[str] = None,
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
        if famiglia and t.famiglia != famiglia:
            continue
        out.append(TipoRelazioneOut(
            id=t.id, codice=t.codice, nome=t.nome_display, modulo=t.modulo_id, fonte=t.fonte,
            entity_types=t.entity_types, scadenza=t.scadenza, unico_per_oggetto=t.unico_per_oggetto,
            sottotipi_fonte=t.sottotipi_fonte, famiglia=t.famiglia,
            ammette_quota=t.ammette_quota, solo_beni=t.solo_beni,
        ))
    return out


@router.get("/", response_model=List[RelazioneOut])
def list_relazioni(
    soggetto_id: Optional[int] = None,
    tipo: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    solo_correnti: bool = Query(False),
    famiglia: Optional[str] = None,
    db: Session = Depends(get_db),
    tenant_schema=Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.view")),
):
    return relazioni_query.elenca(
        db, _schema(tenant_schema), permessi=current_user.get_permissions(),
        soggetto_ids=[soggetto_id] if soggetto_id is not None else None,
        tipo=tipo, entity_type=entity_type, entity_id=entity_id, solo_correnti=solo_correnti,
        famiglia=famiglia,
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
    _verifica_scrittura(current_user, tipo, db, tenant_schema, data.entity_type, data.entity_id)
    _verifica_oggetto(db, tenant_schema, current_user, tipo, data.entity_type, data.entity_id)
    campi = data.model_dump(exclude={"soggetto_id", "tipo"})
    campi["quota"] = _errori(lambda: parse_quota(data.quota)) if data.quota else None
    rel = _errori(lambda: svc.crea(data.soggetto_id, data.tipo, **campi))
    db.commit()
    db.refresh(rel)
    return rel


def _tipo_di(db: Session, relazione_id: int, tenant_schema=None, user: Optional[User] = None,
             lettura: bool = False) -> RuoloDisponibile:
    """Type of a core relation; with `user`, also checks the object permission (403)."""
    rel = db.get(Relazione, relazione_id)
    if rel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Relazione {relazione_id} inesistente")
    tipo = db.get(RuoloDisponibile, rel.ruolo_id)
    if user is not None:
        _verifica_oggetto(db, tenant_schema, user, tipo, rel.entity_type, rel.entity_id, lettura)
    return tipo


def _verifica_scrittura_relazione(db: Session, tenant_schema, user: User, relazione_id: int) -> None:
    tipo = _tipo_di(db, relazione_id, tenant_schema, user)
    rel = db.get(Relazione, relazione_id)
    _verifica_scrittura(user, tipo, db, tenant_schema, rel.entity_type, rel.entity_id)


@router.get("/{relazione_id}", response_model=RelazioneCoreOut)
def get_relazione(
    relazione_id: int,
    db: Session = Depends(get_db),
    tenant_schema=Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.view")),
):
    _tipo_di(db, relazione_id, tenant_schema, current_user, lettura=True)
    return db.get(Relazione, relazione_id)


@router.put("/{relazione_id}", response_model=RelazioneCoreOut)
def update_relazione(
    relazione_id: int,
    data: RelazioneUpdate,
    db: Session = Depends(get_db),
    tenant_schema=Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.edit")),
):
    _verifica_scrittura_relazione(db, tenant_schema, current_user, relazione_id)
    svc = _service(db, tenant_schema, current_user)
    campi = data.model_dump(exclude_unset=True)
    if campi.get("quota"):
        campi["quota"] = _errori(lambda: parse_quota(campi["quota"]))
    rel = _errori(lambda: svc.aggiorna(relazione_id, **campi))
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
    _verifica_scrittura_relazione(db, tenant_schema, current_user, relazione_id)
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
    _verifica_scrittura_relazione(db, tenant_schema, current_user, relazione_id)
    _errori(lambda: _service(db, tenant_schema, current_user).elimina(relazione_id))
    db.commit()
    return None
