"""
Per-tenant module gate: a module's API answers only for tenants where the
module is enabled (app.core.middleware.module_gate). Routes belong to the
module of their endpoint's package, whatever their URL prefix.
"""
import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.core.auth.dependencies import get_current_active_user
from app.core.auth.security import create_access_token
from app.core.auth.models import User
from app.core.database import get_db
from app.core.middleware import module_gate
from app.main import app
from tests.integration.conftest import TEST_TENANT

pytestmark = pytest.mark.integration


def _route(path):
    return next(r for r in app.routes if isinstance(r, APIRoute) and r.path == path)


def test_modulo_della_rotta_dal_pacchetto():
    assert module_gate.modulo_della_rotta(_route("/api/v1/condomini/")) == "immobili"
    # affitti_lungo and gestione_pec mount on /api/v1 with no prefix of their own
    assert module_gate.modulo_della_rotta(_route("/api/v1/affittuari/")) == "affitti_lungo"
    assert module_gate.modulo_della_rotta(_route("/api/v1/pec/caselle/")) == "gestione_pec"
    assert module_gate.modulo_della_rotta(_route("/api/v1/relazioni/tipi")) is None


@pytest.fixture
def http(db_session, monkeypatch):
    attivi = {"value": {"anagrafica_italiana", "immobili"}}
    monkeypatch.setattr(module_gate, "moduli_attivi_tenant", lambda schema: attivi["value"])
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_active_user] = lambda: User(
        id=1, username="a", is_superuser=True, is_active=True, roles=[])
    token = create_access_token(data={"sub": "1", "tenant_schema": TEST_TENANT})
    try:
        with TestClient(app) as client:
            client.headers["Authorization"] = f"Bearer {token}"
            yield client, attivi
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_active_user, None)


def test_modulo_attivo_risponde(http):
    client, _ = http
    assert client.get("/api/v1/condomini/").status_code == 200


def test_modulo_non_attivo_403(http):
    client, attivi = http
    attivi["value"] = {"anagrafica_italiana"}
    res = client.get("/api/v1/condomini/")
    assert res.status_code == 403
    assert res.json()["detail"] == "Modulo immobili non attivo per questo tenant"
    assert client.get("/api/v1/affittuari/").status_code == 403


def test_rotte_di_piattaforma_libere(http):
    client, attivi = http
    attivi["value"] = set()
    assert client.get("/api/v1/relazioni/tipi").status_code == 200


def test_tenant_sconosciuto_403(http):
    client, attivi = http
    attivi["value"] = None
    assert client.get("/api/v1/condomini/").status_code == 403


def test_senza_tenant_decide_l_autenticazione(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        with TestClient(app) as client:
            res = client.get("/api/v1/condomini/")
            assert res.json()["detail"] == "Not authenticated"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_moduli_attivi_tenant_legge_il_db():
    assert "immobili" in module_gate.moduli_attivi_tenant(TEST_TENANT)
    assert module_gate.moduli_attivi_tenant("schema_inesistente") is None
