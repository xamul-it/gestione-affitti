"""
Raggruppamenti (rami) of beni: tree, detail, create, edit/archive, move,
delete, and the ramo's own relations (tenancies, assignments).

Permissions (no new ones): a ramo is seen with immobile.view or terreno.view
and changed with immobile.edit or terreno.edit; inside a ramo only the beni of
the types the user may see are listed. Relations also need soggetto.view /
soggetto.edit, like those of a bene.
"""
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.auth.dependencies import get_current_active_user
from app.core.auth.models import User
from app.core.database import get_db, get_tenant_schema

from ..models import Bene, Raggruppamento
from ..schemas.raggruppamenti import (
    BeneNelRamo, RaggruppamentoCreate, RaggruppamentoDettaglio, RaggruppamentoUpdate, RamoAlbero, RamoBase,
    RamoPiatto, SpostaRaggruppamento,
)
from ..schemas.relazioni_bene import RelazioneBeneCreata, RelazioneBeneCreate, RelazioniBeneResponse
from ..services.raggruppamenti import (
    RamoNonCancellabile, aggiorna_raggruppamento, antenati, cancella_raggruppamento, crea_raggruppamento,
    sposta_raggruppamento,
)
from ..services.relazioni_bene import (
    crea_relazione_raggruppamento, permessi_modifica_ramo, relazioni_del_raggruppamento,
)
from .beni import _tipi_visibili

router = APIRouter(prefix="/raggruppamenti", tags=["Raggruppamenti"])

_VISTA = ("immobile.view", "terreno.view")
_MODIFICA = ("immobile.edit", "terreno.edit")
SEPARATORE = " › "


def _verifica(utente, alternativi, *richiesti) -> None:
    if getattr(utente, "is_superuser", False):
        return
    permessi = utente.get_permissions()
    if not any(p in permessi for p in alternativi) or any(p not in permessi for p in richiesti):
        raise HTTPException(status_code=403, detail="Permessi insufficienti")


def _verifica_eredita(db: Session, utente, ramo: Raggruppamento) -> None:
    """Moving or deleting a ramo, or writing its relations, changes what every bene below inherits:
    the edit permission of each bene type found there is required."""
    if getattr(utente, "is_superuser", False):
        return
    if not permessi_modifica_ramo(db, ramo.id) <= utente.get_permissions():
        raise HTTPException(status_code=403, detail="Permessi insufficienti sui beni del raggruppamento")


def _ramo(db: Session, raggruppamento_id: int) -> Raggruppamento:
    ramo = db.get(Raggruppamento, raggruppamento_id)
    if ramo is None:
        raise HTTPException(status_code=404, detail="Raggruppamento non trovato")
    return ramo


def _errori(fn):
    try:
        return fn()
    except RamoNonCancellabile as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


def _beni_visibili(db: Session, utente, ramo_ids: List[int]) -> Dict[int, List[Bene]]:
    tipi = _tipi_visibili(utente)
    if not tipi or not ramo_ids:
        return {}
    out: Dict[int, List[Bene]] = {}
    for b in (db.query(Bene).filter(Bene.raggruppamento_id.in_(ramo_ids), Bene.tipo_bene.in_(tipi))
              .order_by(Bene.codice)):
        out.setdefault(b.raggruppamento_id, []).append(b)
    return out


def _percorso_testo(per_id: Dict[int, Raggruppamento], ramo: Raggruppamento) -> str:
    nomi, visti, corrente = [], set(), ramo
    while corrente is not None and corrente.id not in visti:
        visti.add(corrente.id)
        nomi.append(corrente.nome)
        corrente = per_id.get(corrente.padre_id)
    return SEPARATORE.join(reversed(nomi))


@router.get("/")
def get_raggruppamenti(
    vista: str = Query("albero", pattern="^(albero|piatta)$"),
    tipo: Optional[str] = Query(None, description="Solo nella vista piatta"),
    includi_archiviati: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Tree (archived rami hide their subtree) or flat list ordered by path."""
    _verifica(current_user, _VISTA)
    tutti = db.query(Raggruppamento).all()
    per_id = {r.id: r for r in tutti}
    visibili = [r for r in tutti if includi_archiviati or r.attivo]
    if vista == "piatta":
        righe = [RamoPiatto(id=r.id, tipo=r.tipo, nome=r.nome, attivo=r.attivo, percorso=_percorso_testo(per_id, r))
                 for r in visibili if tipo is None or r.tipo == tipo]
        return sorted(righe, key=lambda r: r.percorso.lower())
    beni = _beni_visibili(db, current_user, [r.id for r in visibili])
    figli: Dict[Optional[int], List[Raggruppamento]] = {}
    for r in visibili:
        figli.setdefault(r.padre_id, []).append(r)

    def nodo(r: Raggruppamento, profondita: int = 0) -> RamoAlbero:
        sotto = sorted(figli.get(r.id, []), key=lambda x: x.nome.lower()) if profondita < 100 else []
        return RamoAlbero(id=r.id, tipo=r.tipo, nome=r.nome, attivo=r.attivo,
                          figli=[nodo(f, profondita + 1) for f in sotto],
                          beni=[BeneNelRamo.model_validate(b) for b in beni.get(r.id, [])])

    radici = [r for r in visibili if r.padre_id is None or r.padre_id not in per_id]
    return [nodo(r) for r in sorted(radici, key=lambda x: x.nome.lower())]


def _dettaglio(db: Session, ramo: Raggruppamento, utente) -> RaggruppamentoDettaglio:
    percorso = [{"id": r.id, "nome": r.nome, "tipo": r.tipo} for r in antenati(db, ramo.id)]
    figli = sorted(db.query(Raggruppamento).filter(Raggruppamento.padre_id == ramo.id), key=lambda x: x.nome.lower())
    return RaggruppamentoDettaglio(
        id=ramo.id, tipo=ramo.tipo, nome=ramo.nome, attivo=ramo.attivo, descrizione=ramo.descrizione,
        note=ramo.note, padre_id=ramo.padre_id, percorso=percorso,
        figli=[RamoBase(id=f.id, tipo=f.tipo, nome=f.nome, attivo=f.attivo) for f in figli],
        beni=[BeneNelRamo.model_validate(b) for b in _beni_visibili(db, utente, [ramo.id]).get(ramo.id, [])],
    )


@router.get("/{raggruppamento_id}", response_model=RaggruppamentoDettaglio)
def get_raggruppamento(raggruppamento_id: int, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_active_user)):
    _verifica(current_user, _VISTA)
    return _dettaglio(db, _ramo(db, raggruppamento_id), current_user)


@router.post("/", response_model=RaggruppamentoDettaglio, status_code=201)
def create_raggruppamento(dati: RaggruppamentoCreate, db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_active_user)):
    _verifica(current_user, _MODIFICA)
    ramo = _errori(lambda: crea_raggruppamento(db, dati.tipo, dati.nome, dati.padre_id, dati.descrizione, dati.note))
    db.commit()
    return _dettaglio(db, ramo, current_user)


@router.put("/{raggruppamento_id}", response_model=RaggruppamentoDettaglio)
def update_raggruppamento(raggruppamento_id: int, dati: RaggruppamentoUpdate, db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_active_user)):
    _verifica(current_user, _MODIFICA)
    ramo = _ramo(db, raggruppamento_id)
    _errori(lambda: aggiorna_raggruppamento(db, ramo, **dati.model_dump(exclude_unset=True)))
    db.commit()
    return _dettaglio(db, ramo, current_user)


@router.post("/{raggruppamento_id}/sposta", response_model=RaggruppamentoDettaglio)
def move_raggruppamento(raggruppamento_id: int, dati: SpostaRaggruppamento, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_active_user)):
    _verifica(current_user, _MODIFICA)
    ramo = _ramo(db, raggruppamento_id)
    _verifica_eredita(db, current_user, ramo)
    _errori(lambda: sposta_raggruppamento(db, ramo, dati.padre_id))
    db.commit()
    return _dettaglio(db, ramo, current_user)


@router.delete("/{raggruppamento_id}", status_code=204)
def delete_raggruppamento(raggruppamento_id: int, db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_active_user)):
    """Only a ramo with no relations nor documents; its children move to its parent."""
    _verifica(current_user, _MODIFICA)
    ramo = _ramo(db, raggruppamento_id)
    _verifica_eredita(db, current_user, ramo)
    _errori(lambda: cancella_raggruppamento(db, ramo))
    db.commit()
    return Response(status_code=204)


# --- Own relations of the ramo (changing or closing one stays on /relazioni/{id}) ----------

@router.get("/{raggruppamento_id}/relazioni", response_model=RelazioniBeneResponse)
def get_relazioni_raggruppamento(
    raggruppamento_id: int,
    solo_correnti: bool = Query(False),
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(get_current_active_user),
):
    _verifica(current_user, _VISTA, "soggetto.view")
    _ramo(db, raggruppamento_id)
    return relazioni_del_raggruppamento(db, tenant_schema, raggruppamento_id, solo_correnti)


@router.post("/{raggruppamento_id}/relazioni", response_model=RelazioneBeneCreata, status_code=201)
def create_relazione_raggruppamento(
    raggruppamento_id: int,
    dati: RelazioneBeneCreate,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(get_current_active_user),
):
    _verifica(current_user, _MODIFICA, "soggetto.view", "soggetto.edit")
    _verifica_eredita(db, current_user, _ramo(db, raggruppamento_id))
    rel, avvisi = _errori(lambda: crea_relazione_raggruppamento(
        db, tenant_schema, current_user.id, raggruppamento_id, dati.soggetto_id, dati.tipo, quota=dati.quota,
        data_inizio=dati.data_inizio, data_fine=dati.data_fine, note=dati.note, dati=dati.dati,
    ))
    db.commit()
    righe = relazioni_del_raggruppamento(db, tenant_schema, raggruppamento_id)
    riga = next(r for famiglia in righe.values() for r in famiglia if r["id"] == rel.id)
    return {"relazione": riga, "avvisi": avvisi}
