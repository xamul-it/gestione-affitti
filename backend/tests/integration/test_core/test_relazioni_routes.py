"""
/api/v1/relazioni: catalog, listing and core-relation writes with permissions.
"""
import pytest
from fastapi.testclient import TestClient

from anagrafica_italiana.__manifest__ import manifest as anagrafica_manifest
from anagrafica_italiana.models import SoggettoAnagrafico
from anagrafica_italiana.models.soggetto_anagrafico import TipoSoggetto
from affitti_lungo.__manifest__ import manifest as affitti_manifest
from immobili.__manifest__ import manifest as immobili_manifest
from immobili.models import Condominio
from app.core.auth.dependencies import get_current_active_user
from app.core.auth.models import Permission, Role, User
from app.core.database import get_db, get_tenant_schema
from app.core.platform_services.relation_type_sync import sync_relation_types
from app.main import app
from tests.integration.conftest import TEST_TENANT

pytestmark = pytest.mark.integration


def _user(*perms):
    return User(id=1, username="t", is_superuser=False, is_active=True,
                roles=[Role(name="r", permissions=[Permission(name=p) for p in perms])])


@pytest.fixture
def ctx(db_session, unique_suffix):
    sync_relation_types(db_session, {
        "immobili": immobili_manifest, "affitti_lungo": affitti_manifest,
        "anagrafica_italiana": anagrafica_manifest,
    })
    s = SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_FISICA, nome="Mario", cognome="Rossi")
    c = Condominio(codice=f"RR-{unique_suffix}", nome="Aurora", indirizzo="Via Po 1", citta="Torino")
    db_session.add_all([s, c])
    db_session.flush()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_tenant_schema] = lambda: TEST_TENANT
    try:
        with TestClient(app) as client:
            yield client, s, c
    finally:
        for dep in (get_db, get_tenant_schema, get_current_active_user):
            app.dependency_overrides.pop(dep, None)


def _as(*perms):
    app.dependency_overrides[get_current_active_user] = lambda: _user(*perms)


def _body(s, c, **kw):
    return {"soggetto_id": s.id, "tipo": "amministratore_condominio", "entity_type": "CONDOMINIO",
            "entity_id": c.id, "data_inizio": "2026-01-15", **kw}


def test_lettura_richiede_soggetto_view(ctx):
    http, s, _ = ctx
    _as("immobile.view")
    assert http.get(f"/api/v1/relazioni/?soggetto_id={s.id}").status_code == 403
    _as("soggetto.view")
    assert http.get(f"/api/v1/relazioni/?soggetto_id={s.id}").status_code == 200


def test_tipi_per_oggetto(ctx):
    http, _, _ = ctx
    _as("soggetto.view")
    res = http.get("/api/v1/relazioni/tipi?entity_type=CONDOMINIO")
    assert res.status_code == 200
    assert [t["codice"] for t in res.json()] == ["amministratore_condominio"]
    assert res.json()[0]["scadenza"] == {"mesi": 12, "da": "data_inizio"}


def test_crea_richiede_permesso_oggetto(ctx):
    http, s, c = ctx
    _as("soggetto.view", "soggetto.edit")
    assert http.post("/api/v1/relazioni/", json=_body(s, c)).status_code == 403
    _as("soggetto.view", "soggetto.edit", "condominio.edit")
    res = http.post("/api/v1/relazioni/", json=_body(s, c))
    assert res.status_code == 201, res.text
    assert res.json()["data_scadenza"] == "2027-01-15"


def test_secondo_amministratore_422_e_delete(ctx):
    http, s, c = ctx
    _as("soggetto.view", "soggetto.edit", "condominio.edit")
    rel = http.post("/api/v1/relazioni/", json=_body(s, c)).json()
    res = http.post("/api/v1/relazioni/", json=_body(s, c))
    assert res.status_code == 422
    assert "già un amministratore" in res.json()["detail"]
    assert http.post(f"/api/v1/relazioni/{rel['id']}/rinnova").json()["data_scadenza"] == "2028-01-15"
    assert http.put(f"/api/v1/relazioni/{rel['id']}", json={"note": "ok"}).json()["note"] == "ok"
    assert http.delete(f"/api/v1/relazioni/{rel['id']}").status_code == 204
    assert http.delete(f"/api/v1/relazioni/{rel['id']}").status_code == 404


def test_oggetto_inesistente_404(ctx):
    http, s, c = ctx
    _as("soggetto.view", "soggetto.edit", "condominio.edit")
    assert http.post("/api/v1/relazioni/", json=_body(s, c, entity_id=999999999)).status_code == 404


def test_ruolo_azienda_solo_dalla_sua_api(ctx, db_session):
    http, s, _ = ctx
    azienda = SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_GIURIDICA, ragione_sociale="ACME")
    db_session.add(azienda)
    db_session.flush()
    _as("soggetto.view", "soggetto.edit")
    res = http.post("/api/v1/relazioni/", json={"soggetto_id": s.id, "tipo": "ruolo_azienda",
                                               "entity_type": "SOGGETTO_ANAGRAFICO", "entity_id": azienda.id})
    assert res.status_code == 403
    assert "/anagrafica/ruoli-azienda" in res.json()["detail"]


def test_elimina_condominio_rimuove_le_relazioni(ctx):
    http, s, c = ctx
    _as("soggetto.view", "soggetto.edit", "condominio.edit", "condominio.delete")
    rel = http.post("/api/v1/relazioni/", json=_body(s, c)).json()
    assert http.delete(f"/api/v1/condomini/{c.id}").status_code == 204
    assert http.delete(f"/api/v1/relazioni/{rel['id']}").status_code == 404


def test_anagrafica_con_relazioni_non_si_elimina(ctx):
    url = "/api/v1/anagrafica/soggetti-v2/{id}"
    http, s, c = ctx
    _as("soggetto.view", "soggetto.edit", "condominio.edit", "soggetto.delete")
    http.post("/api/v1/relazioni/", json=_body(s, c))
    res = http.delete(url.format(id=s.id))
    assert res.status_code == 400
    assert "relazion" in res.json()["detail"]
