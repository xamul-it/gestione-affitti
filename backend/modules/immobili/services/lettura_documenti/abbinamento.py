"""
Match a read document to a unit, and the differences between what the
document says and what the unit has.

Rule (same as the visura import): comune + foglio + particella + subalterno,
leading zeros ignored. The comune comes as cadastral code (L219) or name and
is resolved through comuni_italia. Without a unique match the user chooses:
candidates are the units on the same comune + foglio + particella, then the
ones at the same address.
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from ...models import UnitaImmobiliare
from ...schemas.visura_import import CampoModifica
from ..visura.text import strip_zeros
from ..visura_import_service import _resolve_comune, normalize_nome

MAX_CANDIDATI = 10
CAMPI_CONFRONTO = ("indirizzo", "piano", "foglio", "particella", "subalterno")


@dataclass
class Abbinamento:
    unita_id: Optional[int]
    candidati: List[dict] = field(default_factory=list)


def _candidato(u: UnitaImmobiliare) -> dict:
    return {"id": u.id, "codice": u.codice, "indirizzo": u.indirizzo, "citta": u.citta,
            "foglio": u.foglio, "particella": u.particella, "subalterno": u.subalterno}


def _indirizzo(value: Optional[str]) -> str:
    # "VIA PO n.3" and "Via Po 3" are the same address.
    return " ".join(re.sub(r"\b(n|civ)\b", " ", normalize_nome(value)).split())


def _citta(db: Session, dati: dict) -> str:
    comune = _resolve_comune(db, dati.get("codice_comune"), dati.get("comune"))
    return normalize_nome(comune.nome if comune else dati.get("comune"))


def abbina_unita(db: Session, dati: dict) -> Abbinamento:
    citta = _citta(db, dati)
    foglio, particella = strip_zeros(dati.get("foglio")), strip_zeros(dati.get("particella"))
    sub = strip_zeros(dati.get("subalterno"))
    stesso_mappale: List[UnitaImmobiliare] = []
    if citta and foglio and particella:
        stesso_mappale = [
            u for u in db.query(UnitaImmobiliare).filter(UnitaImmobiliare.foglio.isnot(None),
                                                         UnitaImmobiliare.particella.isnot(None))
            if normalize_nome(u.citta) == citta and strip_zeros(u.foglio) == foglio
            and strip_zeros(u.particella) == particella
        ]
    esatte = [u for u in stesso_mappale if sub and strip_zeros(u.subalterno) == sub]
    if len(esatte) == 1:
        return Abbinamento(esatte[0].id)
    if esatte:
        return Abbinamento(None, [_candidato(u) for u in esatte[:MAX_CANDIDATI]])

    candidati: Dict[int, UnitaImmobiliare] = {u.id: u for u in stesso_mappale}
    if dati.get("indirizzo") and citta:
        chiave = _indirizzo(dati["indirizzo"])
        for u in db.query(UnitaImmobiliare).all():
            if normalize_nome(u.citta) == citta and _indirizzo(u.indirizzo) == chiave:
                candidati.setdefault(u.id, u)
    return Abbinamento(None, [_candidato(u) for u in list(candidati.values())[:MAX_CANDIDATI]])


def _uguali(campo: str, attuale, nuovo) -> bool:
    if campo in ("foglio", "particella", "subalterno"):
        return strip_zeros(str(attuale) if attuale is not None else None) == strip_zeros(str(nuovo))
    if campo == "indirizzo":
        return _indirizzo(attuale) == _indirizzo(nuovo)
    return normalize_nome(str(attuale) if attuale is not None else "") == normalize_nome(str(nuovo))


def differenze(unita: UnitaImmobiliare, dati: dict) -> List[CampoModifica]:
    """Fields the document knows and the unit has, where they differ. Missing read values never differ."""
    out = []
    for campo in CAMPI_CONFRONTO:
        nuovo = dati.get(campo)
        if nuovo in (None, ""):
            continue
        attuale = getattr(unita, campo)
        if not _uguali(campo, attuale, nuovo):
            out.append(CampoModifica(campo=campo, attuale=attuale, nuovo=nuovo))
    return out
