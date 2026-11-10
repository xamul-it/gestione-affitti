"""
Business roles (person in a company) as core relations of type ruolo_azienda
(spec docs/superpowers/specs/2026-11-10-relazioni-ruoli-soggetti-design.md, 5):
soggetto = persona fisica, object = the persona giuridica, sottotipo = id of
anag_ruoli_azienda_tipi as a string, free-text role in dati["ruolo"].

Keeps the response shape of the legacy /anagrafica/ruoli-azienda API.
"""
from datetime import date
from typing import List, Optional

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.models import RuoloDisponibile
from app.core.platform.models import Relazione

from ..models import RuoloAziendaTipo, SoggettoAnagrafico

TIPO = "ruolo_azienda"
ENTITY = "SOGGETTO_ANAGRAFICO"


def _tipo_id(db: Session) -> Optional[int]:
    row = (db.query(RuoloDisponibile.id)
           .filter(RuoloDisponibile.codice == TIPO, RuoloDisponibile.attivo.is_(True))
           .order_by(RuoloDisponibile.id).first())
    return row[0] if row else None


def query(db: Session):
    return db.query(Relazione).filter(Relazione.ruolo_id == _tipo_id(db))


def campi(ruolo_tipo_id: Optional[int], ruolo: Optional[str], dati: Optional[dict] = None):
    """(sottotipo, dati) for the given tipo id / free text; one of them is required."""
    testo = (ruolo or "").strip() or None
    if ruolo_tipo_id is None and testo is None:
        raise ValueError("Indica il tipo di ruolo o scrivi il ruolo")
    nuovi = {k: v for k, v in (dati or {}).items() if k != "ruolo"}
    if testo and ruolo_tipo_id is None:
        nuovi["ruolo"] = testo
    return (str(ruolo_tipo_id) if ruolo_tipo_id is not None else None), (nuovi or None)


def _tipo_ruolo(db: Session, rel: Relazione) -> Optional[RuoloAziendaTipo]:
    if not rel.sottotipo or not rel.sottotipo.isdigit():
        return None
    return db.get(RuoloAziendaTipo, int(rel.sottotipo))


def _soggetto(db: Session, soggetto_id: int) -> dict:
    s = db.get(SoggettoAnagrafico, soggetto_id)
    return {
        "id": s.id, "tipo_soggetto": getattr(s.tipo_soggetto, "value", s.tipo_soggetto),
        "codice_fiscale": s.codice_fiscale, "partita_iva": s.partita_iva, "nome": s.nome,
        "cognome": s.cognome, "ragione_sociale": s.ragione_sociale,
        "nome_completo": (f"{s.nome or ''} {s.cognome or ''}".strip()
                          if getattr(s.tipo_soggetto, "value", s.tipo_soggetto) == "PERSONA_FISICA"
                          else s.ragione_sociale or ""),
    }


def risposta(db: Session, rel: Relazione) -> dict:
    tipo = _tipo_ruolo(db, rel)
    return {
        "id": rel.id,
        "persona_fisica_id": rel.soggetto_id,
        "persona_giuridica_id": rel.entity_id,
        "ruolo_tipo_id": tipo.id if tipo else None,
        "ruolo_tipo_nome": tipo.nome if tipo else None,
        "ruolo": (rel.dati or {}).get("ruolo") or (tipo.nome if tipo else None),
        "data_inizio": rel.data_inizio,
        "data_fine": rel.data_fine,
        "persona_fisica": _soggetto(db, rel.soggetto_id),
        "persona_giuridica": _soggetto(db, rel.entity_id),
        "created_at": rel.created_at,
        "updated_at": rel.updated_at,
    }


def per_soggetto(db: Session, soggetto_id: int, attivi_only: bool) -> dict:
    def _filtra(q):
        if attivi_only:
            q = q.filter((Relazione.data_fine.is_(None)) | (Relazione.data_fine >= date.today()))
        return [risposta(db, r) for r in q.order_by(Relazione.id).all()]
    return {
        "come_persona": _filtra(query(db).filter(Relazione.soggetto_id == soggetto_id)),
        "come_azienda": _filtra(query(db).filter(Relazione.entity_type == ENTITY, Relazione.entity_id == soggetto_id)),
    }


def sposta_tipo(db: Session, source_id: int, target_id: int) -> int:
    rels: List[Relazione] = query(db).filter(Relazione.sottotipo == str(source_id)).all()
    for r in rels:
        r.sottotipo = str(target_id)
    return len(rels)


def migra_legacy(db: Session, tenant_schema: str) -> dict:
    """Copy anag_ruoli_azienda rows into core_relazioni once (dati.migrato_da)."""
    insp = inspect(db.get_bind())
    if not (insp.has_table("anag_ruoli_azienda", schema=tenant_schema)
            and insp.has_table("core_relazioni", schema=tenant_schema)):
        return {"letti": 0, "creati": 0}
    tipo_id = _tipo_id(db)
    if tipo_id is None:
        return {"letti": 0, "creati": 0, "errore": "tipo ruolo_azienda assente nel catalogo"}
    righe = db.execute(text(
        "SELECT id, persona_fisica_id, persona_giuridica_id, ruolo_tipo_id, ruolo, data_inizio, data_fine "
        "FROM anag_ruoli_azienda ORDER BY id"
    )).all()
    gia = {
        (r.dati or {}).get("migrato_da")
        for r in db.query(Relazione).filter(Relazione.ruolo_id == tipo_id).all()
    }
    creati = 0
    for r in righe:
        if r.id in gia:
            continue
        dati = {"migrato_da": r.id}
        if r.ruolo_tipo_id is None and r.ruolo:
            dati["ruolo"] = r.ruolo
        db.add(Relazione(
            soggetto_id=r.persona_fisica_id, ruolo_id=tipo_id, entity_type=ENTITY,
            entity_id=r.persona_giuridica_id,
            sottotipo=str(r.ruolo_tipo_id) if r.ruolo_tipo_id is not None else None,
            data_inizio=r.data_inizio, data_fine=r.data_fine, dati=dati,
        ))
        creati += 1
    db.flush()
    return {"letti": len(righe), "creati": creati}
