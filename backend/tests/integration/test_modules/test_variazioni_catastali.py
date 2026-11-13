"""
Catastal changes log for manual edits of a unit (PUT /unita-immobiliari/{id})
and its listing (GET /beni/{id}/variazioni-catastali).
"""
from types import SimpleNamespace

import pytest

from immobili.models import UnitaImmobiliare, VariazioneCatastale
from immobili.routes.beni import get_variazioni_catastali
from immobili.routes.immobili import update_unita_immobiliare
from immobili.schemas import UnitaImmobiliareUpdate

pytestmark = pytest.mark.integration

USER = SimpleNamespace(id=7, is_superuser=True, get_permissions=lambda: set())


@pytest.fixture
def unit(db_session):
    u = UnitaImmobiliare(codice="TEST-VAR-1", tipo="Appartamento", indirizzo="VIA ROMA 1", citta="Milano",
                         foglio="1", particella="2", subalterno="3", rendita_catastale=500.0, piano="1")
    db_session.add(u)
    db_session.flush()
    return u


def test_put_logs_manual_change(db_session, unit):
    update_unita_immobiliare(unit.id, UnitaImmobiliareUpdate(rendita_catastale=600.0, note="x"), db=db_session, current_user=USER)
    rows = db_session.query(VariazioneCatastale).filter_by(bene_id=unit.id).all()
    assert [(r.campo, r.valore_precedente, r.valore_nuovo, r.origine, r.documento_id, r.utente_id) for r in rows] == [
        ("rendita_catastale", "500.0", "600.0", "MANUALE", None, 7)
    ]


def test_put_no_change_no_rows(db_session, unit):
    update_unita_immobiliare(unit.id, UnitaImmobiliareUpdate(rendita_catastale=500.0, piano="1"), db=db_session, current_user=USER)
    assert db_session.query(VariazioneCatastale).filter_by(bene_id=unit.id).count() == 0


def test_get_variazioni_newest_first(db_session, unit):
    update_unita_immobiliare(unit.id, UnitaImmobiliareUpdate(rendita_catastale=600.0), db=db_session, current_user=USER)
    update_unita_immobiliare(unit.id, UnitaImmobiliareUpdate(subalterno="4"), db=db_session, current_user=USER)
    res = get_variazioni_catastali(unit.id, db=db_session, current_user=USER)
    assert [r.campo for r in res] == ["subalterno", "rendita_catastale"]


def test_variazioni_requires_authentication():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as http:
        assert http.get("/api/v1/beni/1/variazioni-catastali").status_code in (401, 403)
