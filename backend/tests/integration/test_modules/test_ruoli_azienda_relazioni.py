"""
Business roles (/anagrafica/ruoli-azienda) stored as core relations of type
ruolo_azienda; legacy anag_ruoli_azienda rows copied by the post_sync hook.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from anagrafica_italiana import post_sync
from anagrafica_italiana.__manifest__ import manifest as anagrafica_manifest
from anagrafica_italiana.models import RuoloAziendaTipo, SoggettoAnagrafico
from anagrafica_italiana.models.soggetto_anagrafico import TipoSoggetto
from affitti_lungo.__manifest__ import manifest as affitti_manifest
from immobili.__manifest__ import manifest as immobili_manifest
from app.core.auth.dependencies import get_current_active_user
from app.core.auth.models import User
from app.core.database import get_db, get_tenant_schema
from app.core.platform.models import Relazione
from app.core.platform_services.relation_type_sync import sync_relation_types
from app.main import app
from tests.integration.conftest import TEST_TENANT

pytestmark = pytest.mark.integration

URL = "/api/v1/anagrafica/ruoli-azienda"


@pytest.fixture
def ctx(db_session, unique_suffix):
    db = db_session
    sync_relation_types(db, {"immobili": immobili_manifest, "affitti_lungo": affitti_manifest,
                             "anagrafica_italiana": anagrafica_manifest})
    pf = SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_FISICA, nome="Mario", cognome="Rossi")
    pg = SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_GIURIDICA, ragione_sociale=f"ACME {unique_suffix}")
    t1 = RuoloAziendaTipo(nome=f"Amministratore {unique_suffix}")
    t2 = RuoloAziendaTipo(nome=f"amministratore {unique_suffix} bis")
    db.add_all([pf, pg, t1, t2])
    db.flush()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_tenant_schema] = lambda: TEST_TENANT
    app.dependency_overrides[get_current_active_user] = lambda: User(id=1, username="a", is_superuser=True, is_active=True)
    try:
        with TestClient(app) as client:
            yield client, db, pf, pg, t1, t2
    finally:
        for dep in (get_db, get_tenant_schema, get_current_active_user):
            app.dependency_overrides.pop(dep, None)


def test_crud_su_core_relazioni(ctx):
    http, db, pf, pg, t1, _ = ctx
    res = http.post(f"{URL}/", json={"persona_fisica_id": pf.id, "persona_giuridica_id": pg.id,
                                    "ruolo_tipo_id": t1.id, "data_inizio": "2025-01-01"})
    assert res.status_code == 201, res.text
    body = res.json()
    assert (body["persona_fisica"]["id"], body["persona_giuridica"]["id"]) == (pf.id, pg.id)
    assert body["ruolo_tipo_id"] == t1.id and body["ruolo_tipo_nome"] == t1.nome
    rel = db.get(Relazione, body["id"])
    assert (rel.soggetto_id, rel.entity_type, rel.entity_id, rel.sottotipo) == (pf.id, "SOGGETTO_ANAGRAFICO", pg.id, str(t1.id))

    per = http.get(f"{URL}/soggetto/{pf.id}").json()
    assert [r["id"] for r in per["come_persona"]] == [body["id"]] and per["come_azienda"] == []
    assert [r["id"] for r in http.get(f"{URL}/soggetto/{pg.id}").json()["come_azienda"]] == [body["id"]]

    res = http.put(f"{URL}/{body['id']}", json={"ruolo": "Socio", "data_fine": "2025-12-31"})
    assert res.status_code == 200 and res.json()["ruolo"] == "Socio"
    assert http.get(f"{URL}/soggetto/{pf.id}", params={"attivi_only": True}).json()["come_persona"] == []
    assert http.delete(f"{URL}/{body['id']}").status_code == 204
    assert http.get(f"{URL}/{body['id']}").status_code == 404


def test_testo_libero(ctx):
    http, _, pf, pg, _, _ = ctx
    res = http.post(f"{URL}/", json={"persona_fisica_id": pf.id, "persona_giuridica_id": pg.id, "ruolo": "Segretaria"})
    assert res.status_code == 201 and res.json()["ruolo"] == "Segretaria" and res.json()["ruolo_tipo_id"] is None


def test_validazioni(ctx):
    http, _, pf, pg, t1, _ = ctx
    res = http.post(f"{URL}/", json={"persona_fisica_id": pg.id, "persona_giuridica_id": pf.id, "ruolo_tipo_id": t1.id})
    assert res.status_code in (400, 422)
    res = http.post(f"{URL}/", json={"persona_fisica_id": pf.id, "persona_giuridica_id": pg.id})
    assert res.status_code in (400, 422)


def test_merge_sposta_sottotipo(ctx):
    http, db, pf, pg, t1, t2 = ctx
    rid = http.post(f"{URL}/", json={"persona_fisica_id": pf.id, "persona_giuridica_id": pg.id,
                                    "ruolo_tipo_id": t2.id}).json()["id"]
    res = http.post("/api/v1/anagrafica/domini/ruoli-azienda-tipi/merge", json={"source_id": t2.id, "target_id": t1.id})
    assert res.status_code == 200, res.text
    assert res.json()["associazioni_aggiornate"] == 1
    db.expire_all()
    assert db.get(Relazione, rid).sottotipo == str(t1.id)


def test_post_sync_copia_legacy_una_volta(ctx):
    _, db, pf, pg, t1, _ = ctx
    db.execute(text("""INSERT INTO anag_ruoli_azienda (persona_fisica_id, persona_giuridica_id, ruolo_tipo_id,
                       ruolo, data_inizio, created_at, updated_at)
                       VALUES (:pf, :pg, :t, NULL, '2024-02-01', now(), now()),
                              (:pf, :pg, NULL, 'Consulente', NULL, now(), now())"""),
               {"pf": pf.id, "pg": pg.id, "t": t1.id})
    post_sync(db, TEST_TENANT)
    post_sync(db, TEST_TENANT)
    rels = db.query(Relazione).filter(Relazione.soggetto_id == pf.id).order_by(Relazione.id).all()
    assert [(r.sottotipo, (r.dati or {}).get("ruolo")) for r in rels] == [(str(t1.id), None), (None, "Consulente")]
    assert all((r.dati or {}).get("migrato_da") for r in rels)
