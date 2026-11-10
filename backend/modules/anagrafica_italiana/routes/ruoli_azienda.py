"""
API endpoints for RuoloAzienda (person-company roles).

Since 2026-11-10 the roles are core relations of type ruolo_azienda
(core_relazioni, see services/ruoli_azienda_relazioni.py); paths and response
shape are unchanged. The legacy anag_ruoli_azienda table is read-only.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth.dependencies import require_permission
from app.core.auth.models import User
from app.core.database import get_db, get_tenant_schema
from app.core.platform.models import Relazione
from app.core.platform_services.relazione_service import RelazioneService

from ..schemas.ruolo_azienda import RuoloAziendaCreate, RuoloAziendaResponse, RuoloAziendaUpdate
from ..services import ruoli_azienda_relazioni as ra

router = APIRouter(prefix="/anagrafica/ruoli-azienda", tags=["Ruoli Azienda"])


def _schema(tenant_schema) -> Optional[str]:
    return tenant_schema if isinstance(tenant_schema, str) else None


def _get(db: Session, ruolo_id: int) -> Relazione:
    rel = ra.query(db).filter(Relazione.id == ruolo_id).first()
    if rel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Ruolo azienda con ID {ruolo_id} non trovato")
    return rel


def _errori(fn):
    try:
        return fn()
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


@router.get("/", response_model=List[RuoloAziendaResponse])
def get_all_ruoli_azienda(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_permission("soggetto.view")),
    db: Session = Depends(get_db),
):
    rels = ra.query(db).order_by(Relazione.id).offset(skip).limit(limit).all()
    return [ra.risposta(db, r) for r in rels]


@router.get("/soggetto/{soggetto_id}")
def get_ruoli_by_soggetto(
    soggetto_id: int,
    attivi_only: bool = False,
    current_user: User = Depends(require_permission("soggetto.view")),
    db: Session = Depends(get_db),
):
    """come_persona: ruoli in cui il soggetto lavora; come_azienda: persone che lavorano nel soggetto."""
    from ..models import SoggettoAnagrafico
    if db.get(SoggettoAnagrafico, soggetto_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Soggetto con ID {soggetto_id} non trovato")
    return ra.per_soggetto(db, soggetto_id, attivi_only)


@router.get("/{ruolo_id}", response_model=RuoloAziendaResponse)
def get_ruolo_azienda(
    ruolo_id: int,
    current_user: User = Depends(require_permission("soggetto.view")),
    db: Session = Depends(get_db),
):
    return ra.risposta(db, _get(db, ruolo_id))


@router.post("/", response_model=RuoloAziendaResponse, status_code=status.HTTP_201_CREATED)
def create_ruolo_azienda(
    data: RuoloAziendaCreate,
    current_user: User = Depends(require_permission("soggetto.create")),
    db: Session = Depends(get_db),
    tenant_schema=Depends(get_tenant_schema),
):
    sottotipo, dati = _errori(lambda: ra.campi(data.ruolo_tipo_id, data.ruolo))
    svc = RelazioneService(db, _schema(tenant_schema), current_user.id)
    rel = _errori(lambda: svc.crea(
        data.persona_fisica_id, ra.TIPO, entity_type=ra.ENTITY, entity_id=data.persona_giuridica_id,
        sottotipo=sottotipo, data_inizio=data.data_inizio, data_fine=data.data_fine, dati=dati,
    ))
    db.commit()
    db.refresh(rel)
    return ra.risposta(db, rel)


@router.put("/{ruolo_id}", response_model=RuoloAziendaResponse)
def update_ruolo_azienda(
    ruolo_id: int,
    data: RuoloAziendaUpdate,
    current_user: User = Depends(require_permission("soggetto.edit")),
    db: Session = Depends(get_db),
    tenant_schema=Depends(get_tenant_schema),
):
    rel = _get(db, ruolo_id)
    campi = data.model_dump(exclude_unset=True)
    aggiornamenti = {k: campi[k] for k in ("data_inizio", "data_fine") if k in campi}
    if "ruolo_tipo_id" in campi or "ruolo" in campi:
        attuale_tipo = int(rel.sottotipo) if rel.sottotipo and rel.sottotipo.isdigit() else None
        tipo_id = campi.get("ruolo_tipo_id", attuale_tipo if "ruolo" not in campi else None)
        testo = campi.get("ruolo", (rel.dati or {}).get("ruolo"))
        aggiornamenti["sottotipo"], aggiornamenti["dati"] = _errori(lambda: ra.campi(tipo_id, testo, rel.dati))
    svc = RelazioneService(db, _schema(tenant_schema), current_user.id)
    rel = _errori(lambda: svc.aggiorna(rel.id, **aggiornamenti))
    db.commit()
    db.refresh(rel)
    return ra.risposta(db, rel)


@router.delete("/{ruolo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ruolo_azienda(
    ruolo_id: int,
    current_user: User = Depends(require_permission("soggetto.delete")),
    db: Session = Depends(get_db),
    tenant_schema=Depends(get_tenant_schema),
):
    rel = _get(db, ruolo_id)
    RelazioneService(db, _schema(tenant_schema), current_user.id).elimina(rel.id)
    db.commit()
    return None
