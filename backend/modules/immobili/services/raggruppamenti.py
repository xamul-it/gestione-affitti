"""
Tree of raggruppamenti (rami) of beni — phase 4a of
docs/superpowers/specs/2026-11-10-beni-catastali-design.md ("Raggruppamenti").

- Pure tree: a ramo has at most one parent, a bene at most one ramo; no cycles.
- No dates on membership: the tree is today's tree.
- Archiving (attivo = false) is the normal action and is reversible; nothing
  goes into an archived ramo. Deleting is the exception: only a ramo with no
  relation (open or closed) and no document; its children move up.

Flushes, never commits: the caller owns the transaction.
ValueError = invalid input, LookupError = not found.
"""
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models import Bene, Raggruppamento

ENTITY_TYPE = "RAGGRUPPAMENTO"

# Code -> label. A list in code, not a DB CHECK (like TIPI_COLLEGAMENTO).
TIPI_RAGGRUPPAMENTO: dict[str, str] = {
    "COMPLESSO": "Complesso",
    "EDIFICIO": "Edificio",
    "FONDO": "Fondo",
    "ALTRO": "Altro",
}

CICLO = "Un raggruppamento non può stare dentro se stesso o un suo sottoraggruppamento"
ARCHIVIATO = "Il raggruppamento è archiviato"
NON_CANCELLABILE = "Il raggruppamento ha relazioni o documenti: archivialo"


class RamoNonCancellabile(ValueError):
    """The ramo has relations or documents: it can only be archived (409)."""


def _tipo(tipo: str) -> str:
    if tipo not in TIPI_RAGGRUPPAMENTO:
        raise ValueError(f"Tipo di raggruppamento '{tipo}' non valido")
    return tipo


def _nome(nome: Optional[str]) -> str:
    nome = (nome or "").strip()
    if not nome:
        raise ValueError("Il nome del raggruppamento è obbligatorio")
    return nome


def _destinazione(db: Session, raggruppamento_id: Optional[int]) -> Optional[Raggruppamento]:
    if raggruppamento_id is None:
        return None
    ramo = db.get(Raggruppamento, raggruppamento_id)
    if ramo is None:
        raise LookupError(f"Raggruppamento {raggruppamento_id} inesistente")
    if not ramo.attivo:
        raise ValueError(ARCHIVIATO)
    return ramo


def crea_raggruppamento(db: Session, tipo: str, nome: str, padre_id: Optional[int] = None,
                        descrizione: Optional[str] = None, note: Optional[str] = None) -> Raggruppamento:
    _destinazione(db, padre_id)
    ramo = Raggruppamento(tipo=_tipo(tipo), nome=_nome(nome), padre_id=padre_id, descrizione=descrizione, note=note)
    db.add(ramo)
    db.flush()
    return ramo


def aggiorna_raggruppamento(db: Session, ramo: Raggruppamento, *, tipo: Optional[str] = None,
                            nome: Optional[str] = None, descrizione: Optional[str] = None,
                            note: Optional[str] = None, attivo: Optional[bool] = None) -> Raggruppamento:
    if tipo is not None:
        ramo.tipo = _tipo(tipo)
    if nome is not None:
        ramo.nome = _nome(nome)
    if descrizione is not None:
        ramo.descrizione = descrizione
    if note is not None:
        ramo.note = note
    if attivo is not None:
        ramo.attivo = attivo
    db.flush()
    return ramo


def antenati(db: Session, raggruppamento_id: int) -> list[Raggruppamento]:
    """From the root down to the ramo itself (included); one recursive query."""
    righe = db.execute(text("""
        WITH RECURSIVE su(id, padre_id, livello) AS (
            SELECT id, padre_id, 0 FROM immo_raggruppamenti WHERE id = :id
            UNION ALL
            SELECT r.id, r.padre_id, su.livello + 1
            FROM immo_raggruppamenti r JOIN su ON r.id = su.padre_id
            WHERE su.livello < 100
        )
        SELECT id FROM su ORDER BY livello DESC
    """), {"id": raggruppamento_id}).scalars().all()
    if not righe:
        return []
    per_id = {r.id: r for r in db.query(Raggruppamento).filter(Raggruppamento.id.in_(righe))}
    return [per_id[i] for i in righe]


def discendenti_ids(db: Session, raggruppamento_id: int) -> set[int]:
    """Ids of the ramo and of every ramo below it."""
    return set(db.execute(text("""
        WITH RECURSIVE giu(id, livello) AS (
            SELECT id, 0 FROM immo_raggruppamenti WHERE id = :id
            UNION ALL
            SELECT r.id, giu.livello + 1
            FROM immo_raggruppamenti r JOIN giu ON r.padre_id = giu.id
            WHERE giu.livello < 100
        )
        SELECT id FROM giu
    """), {"id": raggruppamento_id}).scalars().all())


def sposta_raggruppamento(db: Session, ramo: Raggruppamento, padre_id: Optional[int]) -> Raggruppamento:
    if padre_id is not None and padre_id in discendenti_ids(db, ramo.id):
        raise ValueError(CICLO)
    _destinazione(db, padre_id)
    ramo.padre_id = padre_id
    db.flush()
    return ramo


def sposta_bene(db: Session, bene: Bene, raggruppamento_id: Optional[int]) -> Bene:
    _destinazione(db, raggruppamento_id)
    bene.raggruppamento_id = raggruppamento_id
    db.flush()
    return bene


def ha_relazioni_o_documenti(db: Session, raggruppamento_id: int) -> bool:
    params = {"t": ENTITY_TYPE, "id": raggruppamento_id}
    return any(
        db.execute(text(f"SELECT 1 FROM {tabella} WHERE entity_type = :t AND entity_id = :id LIMIT 1"),
                   params).first()
        for tabella in ("core_relazioni", "core_documenti")
    )


def cancella_raggruppamento(db: Session, ramo: Raggruppamento) -> dict:
    """Deletes an empty-of-history ramo; its children (rami and beni) move to its parent."""
    if ha_relazioni_o_documenti(db, ramo.id):
        raise RamoNonCancellabile(NON_CANCELLABILE)
    params = {"id": ramo.id, "padre": ramo.padre_id}
    rami = db.execute(text("UPDATE immo_raggruppamenti SET padre_id = :padre WHERE padre_id = :id"), params).rowcount
    beni = db.execute(text("UPDATE immo_beni SET raggruppamento_id = :padre WHERE raggruppamento_id = :id"),
                      params).rowcount
    db.expire_all()
    db.delete(db.get(Raggruppamento, params["id"]))
    db.flush()
    return {"rami_saliti": rami, "beni_saliti": beni}
