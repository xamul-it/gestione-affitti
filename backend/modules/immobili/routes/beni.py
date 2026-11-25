"""
Common API of the beni (units and land parcels): listing with type filter
and search, detail, cadastral changes. Creating and editing the specific
data stays on /unita-immobiliari and /terreni.
"""
import re
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.auth.dependencies import get_current_active_user
from app.core.auth.models import User
from app.core.database import get_db, get_tenant_schema

from ..models import Bene, CollegamentoBeni, VariazioneCatastale
from ..schemas.bene import BeneResponse
from ..schemas.collegamento_beni import (
    CollegamentiBeneResponse, CollegamentoCreate, CollegamentoOut, CollegamentoUpdate,
)
from ..services.collegamenti_beni import (
    TIPI_COLLEGAMENTO, CollegamentoNonValido, aggiorna_collegamento, avvisi_collegamenti,
    crea_collegamento,
)
from ..schemas.relazioni_bene import (
    RelazioneBeneCreata, RelazioneBeneCreate, RelazioniBeneResponse,
)
from ..services.relazioni_bene import PERMESSO_PER_TIPO, crea_relazione_bene, relazioni_del_bene
from ..services.ruoli_bene import riepilogo_bene
from ..schemas.immobili import VariazioneCatastaleResponse
from ..schemas.riepilogo_bene import RiepilogoBeneResponse

router = APIRouter(prefix="/beni", tags=["Beni"])

_FOGLIO_PARTICELLA = re.compile(r"^\s*0*(\w+)\s*/\s*0*(\w+)\s*$")

# Units are seen with immobile.view, land parcels with terreno.view.
_PERMESSO_PER_TIPO = PERMESSO_PER_TIPO
_PERMESSO_MODIFICA = {"UNITA": "immobile.edit", "TERRENO": "terreno.edit"}


def _tipi_visibili(utente) -> set:
    if getattr(utente, "is_superuser", False):
        return set(_PERMESSO_PER_TIPO)
    permessi = utente.get_permissions()
    return {tipo for tipo, permesso in _PERMESSO_PER_TIPO.items() if permesso in permessi}


def _tipi_o_403(utente) -> set:
    tipi = _tipi_visibili(utente)
    if not tipi:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    return tipi


def _bene_visibile(db: Session, bene_id: int, utente) -> Bene:
    tipi = _tipi_o_403(utente)
    bene = db.get(Bene, bene_id)
    if not bene or bene.tipo_bene not in tipi:
        raise HTTPException(status_code=404, detail="Bene non trovato")
    return bene


@router.get("/", response_model=List[BeneResponse])
def get_beni(
    tipo_bene: Optional[str] = Query(None, pattern="^(UNITA|TERRENO)$"),
    q: Optional[str] = Query(None, description="Codice, indirizzo, comune o foglio/particella (es. 40/154)"),
    attivo: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    tipi = _tipi_o_403(current_user)
    if tipo_bene:
        tipi = tipi & {tipo_bene}
    if not tipi:
        return []
    query = db.query(Bene).filter(Bene.tipo_bene.in_(tipi))
    if attivo is not None:
        query = query.filter(Bene.attivo.is_(attivo))
    if q and q.strip():
        testo = q.strip()
        fp = _FOGLIO_PARTICELLA.match(testo)
        if fp:
            # Leading zeros are ignored, as in the visure matching.
            query = query.filter(
                Bene.foglio.op("~")(f"^0*{re.escape(fp.group(1))}$"),
                Bene.particella.op("~")(f"^0*{re.escape(fp.group(2))}$"),
            )
        else:
            like = f"%{testo}%"
            query = query.filter(or_(
                Bene.codice.ilike(like), Bene.indirizzo.ilike(like), Bene.comune.ilike(like),
            ))
    return query.order_by(Bene.codice).limit(500).all()


@router.get("/{bene_id}", response_model=BeneResponse)
def get_bene(
    bene_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return _bene_visibile(db, bene_id, current_user)


@router.get("/{bene_id}/variazioni-catastali", response_model=List[VariazioneCatastaleResponse])
def get_variazioni_catastali(
    bene_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Storico delle variazioni dei dati catastali del bene, dalla più recente."""
    _bene_visibile(db, bene_id, current_user)
    return (
        db.query(VariazioneCatastale)
        .filter(VariazioneCatastale.bene_id == bene_id)
        .order_by(VariazioneCatastale.created_at.desc(), VariazioneCatastale.id.desc())
        .all()
    )


# The summary shows owners' and tenants' names.
_PERMESSI_RIEPILOGO = ("proprietario.view", "conduttore.view")


@router.get("/{bene_id}/riepilogo", response_model=RiepilogoBeneResponse)
def get_riepilogo(
    bene_id: int,
    data: Optional[date] = Query(None, description="Giorno di riferimento, default oggi"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Chi paga cosa: a chi spetta ciascuna voce alla data, senza importi."""
    bene = _bene_visibile(db, bene_id, current_user)
    if not getattr(current_user, "is_superuser", False):
        permessi = current_user.get_permissions()
        if any(p not in permessi for p in _PERMESSI_RIEPILOGO):
            raise HTTPException(status_code=403, detail="Permessi insufficienti")
    return riepilogo_bene(db, bene, data or date.today())


# --- Links between beni (phase 2b) -------------------------------------------

def _puo_modificare(utente, bene: Bene) -> None:
    if getattr(utente, "is_superuser", False):
        return
    if _PERMESSO_MODIFICA[bene.tipo_bene] not in utente.get_permissions():
        raise HTTPException(status_code=403, detail="Permessi insufficienti")


def _out(collegamento: CollegamentoBeni, bene_id: int) -> CollegamentoOut:
    principale = collegamento.bene_id == bene_id
    tipo = TIPI_COLLEGAMENTO.get(collegamento.tipo, {})
    etichetta = tipo.get("etichetta_principale" if principale else "etichetta_collegato", collegamento.tipo)
    return CollegamentoOut(
        id=collegamento.id,
        tipo=collegamento.tipo,
        questo_e="PRINCIPALE" if principale else "COLLEGATO",
        etichetta=etichetta,
        altro_bene=BeneResponse.model_validate(
            collegamento.bene_collegato if principale else collegamento.bene
        ),
        data_inizio=collegamento.data_inizio,
        data_fine=collegamento.data_fine,
        note=collegamento.note,
        aperto=collegamento.aperto,
    )


def _collegamento_del_bene(db: Session, bene_id: int, collegamento_id: int, utente) -> CollegamentoBeni:
    """Writable link touching the bene; the other bene must be visible too."""
    bene = _bene_visibile(db, bene_id, utente)
    _puo_modificare(utente, bene)
    collegamento = db.get(CollegamentoBeni, collegamento_id)
    if not collegamento or bene_id not in (collegamento.bene_id, collegamento.bene_collegato_id):
        raise HTTPException(status_code=404, detail="Collegamento non trovato")
    altro_id = collegamento.bene_collegato_id if collegamento.bene_id == bene_id else collegamento.bene_id
    altro = db.get(Bene, altro_id)
    if altro.tipo_bene not in _tipi_visibili(utente):
        raise HTTPException(status_code=404, detail="Collegamento non trovato")
    return collegamento


@router.get("/{bene_id}/collegamenti", response_model=CollegamentiBeneResponse)
def get_collegamenti(
    bene_id: int,
    storico: bool = Query(False, description="Anche i collegamenti chiusi"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Beni collegati in entrambe le direzioni; quelli non visibili all'utente spariscono."""
    _bene_visibile(db, bene_id, current_user)
    tipi = _tipi_visibili(current_user)
    query = db.query(CollegamentoBeni).filter(
        or_(CollegamentoBeni.bene_id == bene_id, CollegamentoBeni.bene_collegato_id == bene_id)
    )
    if not storico:
        query = query.filter(CollegamentoBeni.data_fine.is_(None))
    righe = sorted(
        query.all(),
        key=lambda c: (not c.aperto, -(c.data_fine.toordinal() if c.data_fine else 0), c.id),
    )
    collegamenti = [_out(c, bene_id) for c in righe]
    return CollegamentiBeneResponse(
        collegamenti=[c for c in collegamenti if c.altro_bene.tipo_bene in tipi],
        avvisi=avvisi_collegamenti(db, bene_id, date.today()),
    )


@router.post("/{bene_id}/collegamenti", response_model=CollegamentoOut, status_code=201)
def create_collegamento(
    bene_id: int,
    dati: CollegamentoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    bene = _bene_visibile(db, bene_id, current_user)
    _puo_modificare(current_user, bene)
    _bene_visibile(db, dati.altro_bene_id, current_user)
    principale, collegato = (bene_id, dati.altro_bene_id) if dati.questo_e == "PRINCIPALE" \
        else (dati.altro_bene_id, bene_id)
    try:
        collegamento = crea_collegamento(db, principale, collegato, dati.tipo, dati.data_inizio, dati.note)
    except CollegamentoNonValido as e:
        raise HTTPException(status_code=400, detail=str(e))
    db.commit()
    return _out(collegamento, bene_id)


@router.put("/{bene_id}/collegamenti/{collegamento_id}", response_model=CollegamentoOut)
def update_collegamento(
    bene_id: int,
    collegamento_id: int,
    dati: CollegamentoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Periodo e note; chiudere = data di fine, riaprire = data di fine vuota."""
    collegamento = _collegamento_del_bene(db, bene_id, collegamento_id, current_user)
    valori = {"data_inizio": collegamento.data_inizio, "data_fine": collegamento.data_fine,
              "note": collegamento.note, **dati.model_dump(exclude_unset=True)}
    try:
        aggiorna_collegamento(db, collegamento, valori["data_inizio"], valori["data_fine"], valori["note"])
    except CollegamentoNonValido as e:
        raise HTTPException(status_code=400, detail=str(e))
    db.commit()
    return _out(collegamento, bene_id)


@router.delete("/{bene_id}/collegamenti/{collegamento_id}", status_code=204)
def delete_collegamento(
    bene_id: int,
    collegamento_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    collegamento = _collegamento_del_bene(db, bene_id, collegamento_id, current_user)
    db.delete(collegamento)
    db.commit()
    return Response(status_code=204)


# --- Relations of the bene (rights, tenancies, assignments) -------------------
# Changing or closing one stays on /relazioni/{id}.

def _bene_per_relazioni(db: Session, bene_id: int, utente, scrittura: bool = False) -> Bene:
    """The bene, if the user may see it (403 otherwise, as the generic relations API) and,
    for writes, edit it (immobile.edit for units, terreno.edit for land parcels). Like the generic
    API, reading needs soggetto.view and writing soggetto.edit."""
    bene = db.get(Bene, bene_id)
    if bene is None:
        raise HTTPException(status_code=404, detail="Bene non trovato")
    if getattr(utente, "is_superuser", False):
        return bene
    permessi = utente.get_permissions()
    # Same gate as the generic /relazioni API: soggetto.view to read, soggetto.edit to write.
    richiesti = [_PERMESSO_PER_TIPO[bene.tipo_bene], "soggetto.view"]
    if scrittura:
        richiesti += [_PERMESSO_MODIFICA[bene.tipo_bene], "soggetto.edit"]
    if any(p not in permessi for p in richiesti):
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    return bene


@router.get("/{bene_id}/relazioni", response_model=RelazioniBeneResponse)
def get_relazioni_bene(
    bene_id: int,
    solo_correnti: bool = Query(False, description="Solo le relazioni non chiuse"),
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(get_current_active_user),
):
    """Diritti, godimento e incarichi del bene, per famiglia."""
    _bene_per_relazioni(db, bene_id, current_user)
    return relazioni_del_bene(db, tenant_schema, bene_id, solo_correnti)


@router.post("/{bene_id}/relazioni", response_model=RelazioneBeneCreata, status_code=201)
def create_relazione_bene(
    bene_id: int,
    dati: RelazioneBeneCreate,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(get_current_active_user),
):
    _bene_per_relazioni(db, bene_id, current_user, scrittura=True)
    try:
        rel, avvisi = crea_relazione_bene(
            db, tenant_schema, current_user.id, bene_id, dati.soggetto_id, dati.tipo, quota=dati.quota,
            data_inizio=dati.data_inizio, data_fine=dati.data_fine, note=dati.note, dati=dati.dati,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    db.commit()
    riga = next(r for righe in relazioni_del_bene(db, tenant_schema, bene_id).values() for r in righe if r["id"] == rel.id)
    return {"relazione": riga, "avvisi": avvisi}
