"""
GET /anagrafica/soggetti-v2/: ?ruolo= prefilter and computed `ruoli`
(from core relations and module providers).
"""
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from anagrafica_italiana.__manifest__ import manifest as anagrafica_manifest
from anagrafica_italiana.models import SoggettoAnagrafico
from anagrafica_italiana.models.soggetto_anagrafico import TipoSoggetto
from affitti_lungo.__manifest__ import manifest as affitti_manifest
from immobili.__manifest__ import manifest as immobili_manifest
from immobili.models import AssegnazioneConduttore, Condominio, Conduttore, Proprietario, UnitaImmobiliare
from app.core.auth.dependencies import get_current_active_user
from app.core.auth.models import Permission, Role, User
from app.core.database import engine, get_db, get_tenant_schema
from app.core.platform_services.relation_type_sync import sync_relation_types
from app.core.platform_services.relazione_service import RelazioneService
from app.main import app
from tests.integration.conftest import TEST_TENANT

pytestmark = pytest.mark.integration

URL = "/api/v1/anagrafica/soggetti-v2/"


def _as(*perms, superuser=False):
    app.dependency_overrides[get_current_active_user] = lambda: User(
        id=1, username="t", is_superuser=superuser, is_active=True,
        roles=[Role(name="r", permissions=[Permission(name=p) for p in perms])])


@pytest.fixture
def ctx(db_session, unique_suffix):
    db = db_session
    sync_relation_types(db, {"immobili": immobili_manifest, "affitti_lungo": affitti_manifest,
                             "anagrafica_italiana": anagrafica_manifest})
    mk = lambda n: SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_FISICA, nome=n, cognome=f"T{unique_suffix}")
    prop, ex_cond, altro = mk("Prop"), mk("ExCond"), mk("Altro")
    db.add_all([prop, ex_cond, altro])
    db.flush()
    db.add(Proprietario(soggetto_id=prop.id))
    u = UnitaImmobiliare(codice=f"SV-{unique_suffix}", tipo="Appartamento", indirizzo="Via A 1", citta="Roma")
    c = Conduttore(soggetto_id=ex_cond.id)
    cond = Condominio(codice=f"SV-{unique_suffix}", nome="Aurora", indirizzo="Via A 1", citta="Roma")
    db.add_all([u, c, cond])
    db.flush()
    db.add(AssegnazioneConduttore(bene_id=u.id, conduttore_id=c.id,
                                  data_inizio=date(2018, 1, 1), data_fine=date(2019, 1, 1)))
    RelazioneService(db, TEST_TENANT).crea(prop.id, "amministratore_condominio", entity_type="CONDOMINIO",
                                          entity_id=cond.id, data_inizio=date(2026, 1, 1))
    db.flush()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_tenant_schema] = lambda: TEST_TENANT
    _as(superuser=True)
    try:
        with TestClient(app) as client:
            yield client, prop, ex_cond, altro
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_tenant_schema, None)
        app.dependency_overrides.pop(get_current_active_user, None)


def _ids(res):
    return {s["id"] for s in res.json()}


def test_filtro_ruolo(ctx):
    http, prop, ex_cond, altro = ctx
    ids = _ids(http.get(URL, params={"ruolo": "proprietario", "limit": 5000}))
    assert prop.id in ids and altro.id not in ids and ex_cond.id not in ids


def test_filtro_ruolo_cessati(ctx):
    http, prop, ex_cond, altro = ctx
    assert ex_cond.id not in _ids(http.get(URL, params={"ruolo": "conduttore", "limit": 5000}))
    ids = _ids(http.get(URL, params={"ruolo": "conduttore", "ruolo_anche_cessati": "true", "limit": 5000}))
    assert ex_cond.id in ids


def test_ruoli_calcolati(ctx):
    http, prop, ex_cond, altro = ctx
    by_id = {s["id"]: s for s in http.get(URL, params={"limit": 5000}).json()}
    assert {r["codice"]: r["n"] for r in by_id[prop.id]["ruoli"]} == {
        "proprietario": 1, "amministratore_condominio": 1,
    }
    assert by_id[ex_cond.id]["ruoli"] == [{"codice": "conduttore", "nome": "Conduttore", "modulo": "immobili", "n": 0}]
    assert by_id[altro.id]["ruoli"] == []


def _count_queries(fn):
    n = [0]

    def before(*_a, **_k):
        n[0] += 1
    event.listen(engine, "before_cursor_execute", before)
    try:
        fn()
    finally:
        event.remove(engine, "before_cursor_execute", before)
    return n[0]


def test_ruoli_senza_query_per_soggetto(ctx):
    http, *_ = ctx
    small = _count_queries(lambda: http.get(URL, params={"limit": 3}))
    big = _count_queries(lambda: http.get(URL, params={"limit": 50}))
    assert big == small


def test_elenco_richiede_soggetto_view(ctx):
    http, prop, *_ = ctx
    _as("immobile.view")
    assert http.get(URL).status_code == 403
    assert http.get(f"{URL}{prop.id}").status_code == 403
    _as("soggetto.view")
    assert http.get(URL).status_code == 200


def test_scritture_richiedono_permesso(ctx):
    http, prop, *_ = ctx
    _as("soggetto.view")
    assert http.post(URL, json={"tipo_soggetto": "PERSONA_FISICA", "nome": "X", "cognome": "Y"}).status_code == 403
    assert http.put(f"{URL}{prop.id}", json={"note": "x"}).status_code == 403
    assert http.delete(f"{URL}{prop.id}").status_code == 403


def test_ruoli_senza_permesso_oggetto_non_si_vedono(ctx):
    http, prop, ex_cond, altro = ctx
    _as("soggetto.view", "condominio.view")
    by_id = {s["id"]: s for s in http.get(URL, params={"limit": 5000}).json()}
    assert [r["codice"] for r in by_id[prop.id]["ruoli"]] == ["amministratore_condominio"]
    assert by_id[ex_cond.id]["ruoli"] == []
    assert _ids(http.get(URL, params={"ruolo": "proprietario", "limit": 5000})) == set()
