"""
Links between beni: types, rules and warnings.

Phase 2b of docs/superpowers/specs/2026-11-10-beni-catastali-design.md
("Collegamenti tra beni"). The type list lives here, not in a DB CHECK, so
a new type needs no migration. Every check runs before the flush so the
user gets the right message; the partial unique indexes stay as the last
guard against two concurrent requests.
"""
from collections import defaultdict
from datetime import date
from typing import Callable, Optional

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.models import RuoloDisponibile
from app.core.platform.models import Relazione

from ..models import Bene, CollegamentoBeni

CATEGORIE_PERTINENZA = ("C/2", "C/6", "C/7")


class CollegamentoNonValido(ValueError):
    """A link that breaks a rule; the route turns it into a 400 with str(e)."""


def _categoria(bene: Bene) -> Optional[str]:
    if bene.tipo_bene != "UNITA":
        return None
    categoria = getattr(bene, "categoria_catastale", None)
    return categoria.codice if categoria else None


def _abitazione(bene: Bene) -> bool:
    categoria = _categoria(bene)
    return bool(categoria) and categoria.startswith("A/") and categoria != "A/10"


def _verifica_pertinenza(principale: Bene, collegato: Bene) -> Optional[str]:
    if not _abitazione(principale):
        return "Una pertinenza si collega a un'abitazione (categoria A, tranne A/10)"
    if _categoria(collegato) not in CATEGORIE_PERTINENZA:
        return "Pertinenza: serve un'unità di categoria C/2, C/6 o C/7"
    return None


def _verifica_fabbricato(principale: Bene, collegato: Bene) -> Optional[str]:
    if principale.tipo_bene != "TERRENO" or collegato.tipo_bene != "UNITA":
        return "Fabbricato su particella: il principale è un terreno, il collegato un'unità"
    return None


def _verifica_fondo(principale: Bene, collegato: Bene) -> Optional[str]:
    if principale.tipo_bene != "TERRENO" or collegato.tipo_bene != "TERRENO":
        return "Parte di fondo: collega due terreni"
    return None


TIPI_COLLEGAMENTO: dict[str, dict] = {
    "PERTINENZA": {
        "etichetta_principale": "Pertinenze",
        "etichetta_collegato": "Pertinenza di",
        "verifica": _verifica_pertinenza,
    },
    "FABBRICATO_SU_PARTICELLA": {
        "etichetta_principale": "Fabbricati sulla particella",
        "etichetta_collegato": "Costruito sulla particella",
        "verifica": _verifica_fabbricato,
    },
    "PARTE_DI_FONDO": {
        "etichetta_principale": "Particelle del fondo",
        "etichetta_collegato": "Parte del fondo di",
        "verifica": _verifica_fondo,
    },
}


def _aperti(db: Session):
    return db.query(CollegamentoBeni).filter(CollegamentoBeni.data_fine.is_(None))


def _controlla_unicita(db: Session, principale: Bene, collegato: Bene, tipo: str,
                       escludi_id: Optional[int] = None) -> None:
    query = _aperti(db).filter(
        CollegamentoBeni.bene_id == principale.id,
        CollegamentoBeni.bene_collegato_id == collegato.id,
        CollegamentoBeni.tipo == tipo,
    )
    if escludi_id:
        query = query.filter(CollegamentoBeni.id != escludi_id)
    if query.first():
        raise CollegamentoNonValido("Collegamento già presente")
    if tipo == "PERTINENZA":
        query = _aperti(db).filter(
            CollegamentoBeni.tipo == "PERTINENZA",
            CollegamentoBeni.bene_collegato_id == collegato.id,
        )
        if escludi_id:
            query = query.filter(CollegamentoBeni.id != escludi_id)
        altra = query.first()
        if altra:
            raise CollegamentoNonValido(
                f"'{collegato.codice}' è già pertinenza di '{altra.bene.codice}'"
            )


def _flush(db: Session, collegamento: CollegamentoBeni) -> CollegamentoBeni:
    savepoint = db.begin_nested()
    try:
        db.add(collegamento)
        db.flush()
    except IntegrityError:
        savepoint.rollback()
        raise CollegamentoNonValido("Collegamento già presente")
    savepoint.commit()
    return collegamento


def _controlla_date(data_inizio: Optional[date], data_fine: Optional[date]) -> None:
    if data_inizio and data_fine and data_fine < data_inizio:
        raise CollegamentoNonValido("La data di fine precede quella di inizio")


def crea_collegamento(db: Session, principale_id: int, collegato_id: int, tipo: str,
                      data_inizio: Optional[date], note: Optional[str]) -> CollegamentoBeni:
    """New open link principal -> linked; the caller commits."""
    regole = TIPI_COLLEGAMENTO.get(tipo)
    if not regole:
        raise CollegamentoNonValido(f"Tipo di collegamento sconosciuto: {tipo}")
    if principale_id == collegato_id:
        raise CollegamentoNonValido("Un bene non si collega a sé stesso")
    principale, collegato = db.get(Bene, principale_id), db.get(Bene, collegato_id)
    if principale is None or collegato is None:
        raise CollegamentoNonValido("Bene non trovato")
    verifica: Callable = regole["verifica"]
    errore = verifica(principale, collegato)
    if errore:
        raise CollegamentoNonValido(errore)
    _controlla_unicita(db, principale, collegato, tipo)
    return _flush(db, CollegamentoBeni(
        bene_id=principale.id, bene_collegato_id=collegato.id, tipo=tipo,
        data_inizio=data_inizio, note=note,
    ))


def aggiorna_collegamento(db: Session, collegamento: CollegamentoBeni, data_inizio: Optional[date],
                          data_fine: Optional[date], note: Optional[str]) -> CollegamentoBeni:
    """Change period and notes (the two beni and the type stay); the caller commits."""
    _controlla_date(data_inizio, data_fine)
    if data_fine is None and collegamento.data_fine is not None:
        _controlla_unicita(db, collegamento.bene, collegamento.bene_collegato, collegamento.tipo,
                           escludi_id=collegamento.id)
    collegamento.data_inizio = data_inizio
    collegamento.data_fine = data_fine
    collegamento.note = note
    return _flush(db, collegamento)


def _titolari_oggi(db: Session, bene_id: int, oggi: date) -> set[int]:
    """Soggetti holding a real right (relation of the diritti_reali family) on the bene on that day."""
    return {
        r[0] for r in db.query(Relazione.soggetto_id)
        .join(RuoloDisponibile, RuoloDisponibile.id == Relazione.ruolo_id)
        .filter(
            Relazione.entity_type == "IMMOBILE", Relazione.entity_id == bene_id,
            RuoloDisponibile.modulo_id == "immobili", RuoloDisponibile.famiglia == "diritti_reali",
            or_(Relazione.data_inizio.is_(None), Relazione.data_inizio <= oggi),
            or_(Relazione.data_fine.is_(None), Relazione.data_fine >= oggi),
        )
    }


def _avviso_categoria(categoria: str) -> str:
    return (f"Più pertinenze di categoria {categoria}: per l'IMU dell'abitazione principale "
            "ne conta una per categoria (L. 160/2019, c. 741)")


def _avviso_titolari(codice: str) -> str:
    return f"Titolari di '{codice}' diversi da quelli dell'abitazione"


def _pertinenze_aperte(db: Session, abitazione_id: int) -> list[CollegamentoBeni]:
    return _aperti(db).filter(
        CollegamentoBeni.tipo == "PERTINENZA", CollegamentoBeni.bene_id == abitazione_id
    ).order_by(CollegamentoBeni.id).all()


def avvisi_collegamenti(db: Session, bene_id: int, oggi: date) -> list[str]:
    """Non-blocking warnings for the bene, as a dwelling and as a pertinenza.

    Different holders: compared only when both beni have holders on that day,
    so a bene whose rights are not registered yet raises no warning.
    """
    avvisi: list[str] = []

    pertinenze = _pertinenze_aperte(db, bene_id)
    if pertinenze:
        per_categoria = defaultdict(int)
        for c in pertinenze:
            per_categoria[_categoria(c.bene_collegato)] += 1
        avvisi += [_avviso_categoria(cat) for cat, n in sorted(per_categoria.items()) if cat and n > 1]
        titolari = _titolari_oggi(db, bene_id, oggi)
        for c in pertinenze:
            suoi = _titolari_oggi(db, c.bene_collegato_id, oggi)
            if titolari and suoi and suoi != titolari:
                avvisi.append(_avviso_titolari(c.bene_collegato.codice))

    come_pertinenza = _aperti(db).filter(
        CollegamentoBeni.tipo == "PERTINENZA", CollegamentoBeni.bene_collegato_id == bene_id
    ).first()
    if come_pertinenza:
        mia = _categoria(come_pertinenza.bene_collegato)
        sorelle = _pertinenze_aperte(db, come_pertinenza.bene_id)
        if mia and sum(1 for c in sorelle if _categoria(c.bene_collegato) == mia) > 1:
            avvisi.append(_avviso_categoria(mia))
        titolari = _titolari_oggi(db, come_pertinenza.bene_id, oggi)
        suoi = _titolari_oggi(db, bene_id, oggi)
        if titolari and suoi and suoi != titolari:
            avvisi.append(_avviso_titolari(come_pertinenza.bene_collegato.codice))
    return avvisi


def ruoli_pertinenza(db: Session, bene_ids: list[int]) -> dict[int, str]:
    """bene_id -> "PERTINENZA" | "CON_PERTINENZE" for open pertinenze, one query."""
    if not bene_ids:
        return {}
    ruoli: dict[int, str] = {}
    for principale, collegato in db.query(CollegamentoBeni.bene_id, CollegamentoBeni.bene_collegato_id).filter(
        CollegamentoBeni.tipo == "PERTINENZA",
        CollegamentoBeni.data_fine.is_(None),
        or_(CollegamentoBeni.bene_id.in_(bene_ids), CollegamentoBeni.bene_collegato_id.in_(bene_ids)),
    ):
        ruoli[collegato] = "PERTINENZA"
        ruoli.setdefault(principale, "CON_PERTINENZE")
    return ruoli
