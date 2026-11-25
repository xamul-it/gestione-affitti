"""
immo_beni_collegamenti: links between beni (phase 2b of
docs/superpowers/specs/2026-11-10-beni-catastali-design.md).
"""
import importlib.util
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from immobili.models import CollegamentoBeni, UnitaImmobiliare

MIGRAZIONE_BENI = (
    Path(__file__).resolve().parents[4]
    / "modules" / "immobili" / "migrations" / "2026111201_beni.py"
)


def _unita(db, codice):
    u = UnitaImmobiliare(codice=codice, tipo="Appartamento", indirizzo="Via A 1", citta="Forlì")
    db.add(u)
    db.flush()
    return u


def test_indici_parziali_presenti(db_session):
    nomi = {r[0] for r in db_session.execute(text(
        "SELECT indexname FROM pg_indexes WHERE schemaname = current_schema() "
        "AND tablename = 'immo_beni_collegamenti'"
    ))}
    assert {"uq_immo_beni_collegamenti_aperto", "uq_immo_beni_pertinenza_aperta"} <= nomi


def test_stessa_pertinenza_due_abitazioni_viola_indice(db_session):
    a, b, box = (_unita(db_session, c) for c in ("COLL-M-A", "COLL-M-B", "COLL-M-BOX"))
    primo = CollegamentoBeni(bene_id=a.id, bene_collegato_id=box.id, tipo="PERTINENZA")
    db_session.add(primo)
    db_session.flush()
    assert primo.aperto is True

    sp = db_session.begin_nested()
    db_session.add(CollegamentoBeni(bene_id=b.id, bene_collegato_id=box.id, tipo="PERTINENZA"))
    with pytest.raises(IntegrityError):
        db_session.flush()
    sp.rollback()

    primo.data_fine = date(2026, 1, 1)
    db_session.flush()
    assert primo.aperto is False
    db_session.add(CollegamentoBeni(bene_id=b.id, bene_collegato_id=box.id, tipo="PERTINENZA"))
    db_session.flush()


def test_bene_non_si_collega_a_se_stesso(db_session):
    a = _unita(db_session, "COLL-M-SE")
    sp = db_session.begin_nested()
    db_session.add(CollegamentoBeni(bene_id=a.id, bene_collegato_id=a.id, tipo="PERTINENZA"))
    with pytest.raises(IntegrityError):
        db_session.flush()
    sp.rollback()


def test_azzera_con_collegamenti(db_session):
    a, box = _unita(db_session, "COLL-M-AZ"), _unita(db_session, "COLL-M-AZB")
    db_session.add(CollegamentoBeni(bene_id=a.id, bene_collegato_id=box.id, tipo="PERTINENZA"))
    db_session.flush()
    spec = importlib.util.spec_from_file_location("migrazione_beni_coll", MIGRAZIONE_BENI)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    risultato = modulo.azzera(db_session.connection())
    assert "immo_beni_collegamenti" in risultato
    assert db_session.execute(text("SELECT count(*) FROM immo_beni_collegamenti")).scalar() == 0
