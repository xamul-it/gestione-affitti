"""
Common listing and detail of beni (GET /beni, /beni/{id}), phase 2a of
docs/superpowers/specs/2026-11-10-beni-catastali-design.md.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from immobili.models import Terreno, TerrenoPorzione, UnitaImmobiliare
from immobili.routes.beni import get_bene, get_beni, get_variazioni_catastali

pytestmark = pytest.mark.integration

UTENTE = SimpleNamespace(id=1)


@pytest.fixture
def beni(db_session):
    u = UnitaImmobiliare(codice="BAPI-U", tipo="Appartamento", indirizzo="Via Zanzibar 1", citta="Forlì")
    t = Terreno(codice="BAPI-T", comune="Forlì", provincia="FC", foglio="40", particella="154",
                porzioni=[TerrenoPorzione(qualita="SEMINATIVO", superficie_mq=10)])
    db_session.add_all([u, t])
    db_session.flush()
    return u, t


def _codici(risposta):
    return {b.codice for b in risposta}


def test_beni_elenco_filtra_e_cerca(db_session, beni):
    u, t = beni
    tutti = get_beni(tipo_bene=None, q="BAPI", attivo=None, db=db_session, current_user=UTENTE)
    assert _codici(tutti) == {"BAPI-U", "BAPI-T"}
    assert _codici(get_beni(tipo_bene="TERRENO", q="BAPI", attivo=None, db=db_session, current_user=UTENTE)) == {"BAPI-T"}
    assert "BAPI-T" in _codici(get_beni(tipo_bene=None, q="40/154", attivo=None, db=db_session, current_user=UTENTE))
    assert "BAPI-U" not in _codici(get_beni(tipo_bene=None, q="40/154", attivo=None, db=db_session, current_user=UTENTE))
    assert _codici(get_beni(tipo_bene=None, q="zanzibar", attivo=None, db=db_session, current_user=UTENTE)) == {"BAPI-U"}
    assert get_bene(u.id, db=db_session, current_user=UTENTE).tipo_bene == "UNITA"
    assert get_bene(t.id, db=db_session, current_user=UTENTE).foglio == "40"


def test_beni_filtro_attivo(db_session, beni):
    u, t = beni
    t.attivo = False
    db_session.flush()
    assert _codici(get_beni(tipo_bene=None, q="BAPI", attivo=True, db=db_session, current_user=UTENTE)) == {"BAPI-U"}
    assert _codici(get_beni(tipo_bene=None, q="BAPI", attivo=False, db=db_session, current_user=UTENTE)) == {"BAPI-T"}


def test_bene_inesistente_404(db_session):
    with pytest.raises(HTTPException) as e:
        get_bene(999999999, db=db_session, current_user=UTENTE)
    assert e.value.status_code == 404
    assert e.value.detail == "Bene non trovato"


def test_variazioni_del_terreno(db_session, beni):
    _, t = beni
    assert get_variazioni_catastali(t.id, db=db_session, current_user=UTENTE) == []
