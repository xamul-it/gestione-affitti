"""
Matching a read document to a unit (single upload point, spec
2026-11-10-caricamento-unico-documenti-immobili): comune + foglio +
particella + subalterno; otherwise candidates for the user to choose.
"""
import pytest

from immobili.models import UnitaImmobiliare
from immobili.schemas.visura_import import CampoModifica
from immobili.services.lettura_documenti.abbinamento import abbina_unita, differenze

pytestmark = pytest.mark.integration


def _unita(db, codice, citta="Torino", foglio="12", particella="345", sub="6", indirizzo="Via Po 3", piano="2"):
    u = UnitaImmobiliare(codice=codice, tipo="Appartamento", indirizzo=indirizzo, citta=citta,
                         foglio=foglio, particella=particella, subalterno=sub, piano=piano)
    db.add(u)
    db.flush()
    return u


DATI = {"codice_comune": "L219", "comune": "TORINO", "foglio": "12", "particella": "345", "subalterno": "6"}


def test_abbina_per_catasto_e_codice_comune(db_session, unique_suffix):
    u = _unita(db_session, f"AB1-{unique_suffix}", foglio="012")
    assert abbina_unita(db_session, DATI).unita_id == u.id


def test_abbina_per_nome_comune(db_session, unique_suffix):
    u = _unita(db_session, f"AB2-{unique_suffix}")
    dati = {k: v for k, v in DATI.items() if k != "codice_comune"}
    assert abbina_unita(db_session, dati).unita_id == u.id


def test_stesso_catasto_altro_comune_non_abbina(db_session, unique_suffix):
    _unita(db_session, f"AB3-{unique_suffix}", citta="Milano")
    a = abbina_unita(db_session, DATI)
    assert a.unita_id is None and a.candidati == []


def test_nessuna_unita_propone_stesso_foglio_particella(db_session, unique_suffix):
    u = _unita(db_session, f"AB4-{unique_suffix}", sub="7")
    a = abbina_unita(db_session, DATI)
    assert a.unita_id is None
    assert [c["id"] for c in a.candidati] == [u.id]


def test_piu_unita_restituisce_candidati(db_session, unique_suffix):
    u1 = _unita(db_session, f"AB5-{unique_suffix}")
    u2 = _unita(db_session, f"AB6-{unique_suffix}")
    a = abbina_unita(db_session, DATI)
    assert a.unita_id is None
    assert {c["id"] for c in a.candidati} == {u1.id, u2.id}


def test_differenze_ignora_zeri_e_maiuscole(db_session, unique_suffix):
    u = _unita(db_session, f"AB7-{unique_suffix}", foglio="012", indirizzo="VIA PO 3")
    assert differenze(u, {**DATI, "indirizzo": "via po 3", "piano": "2"}) == []


def test_differenze_indirizzo_diverso(db_session, unique_suffix):
    u = _unita(db_session, f"AB8-{unique_suffix}", indirizzo="Via Po 1")
    assert differenze(u, {**DATI, "indirizzo": "VIA PO 3"}) == [
        CampoModifica(campo="indirizzo", attuale="Via Po 1", nuovo="VIA PO 3")
    ]
