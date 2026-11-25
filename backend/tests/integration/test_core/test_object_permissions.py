"""
Per-object permission hook (manifest `object_permissions`): a module can
decide, per object, which permission is needed to see/touch the relations
pointing at it. The hook returns a select of (entity_id, permesso) and is
joined in SQL: one hook call per listing.
"""
import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from anagrafica_italiana.models import SoggettoAnagrafico
from anagrafica_italiana.models.soggetto_anagrafico import TipoSoggetto
from app.core.auth.dependencies import get_current_active_user
from app.core.auth.models import Permission, Role, User
from app.core.database import get_db, get_tenant_schema
from app.core.models.tenant import Tenant, TenantModule
from app.core.platform_services import object_permissions
from app.core.platform_services.relation_type_sync import sync_relation_types
from app.main import app
from immobili.models import Condominio
from tests.integration.conftest import TEST_TENANT

pytestmark = pytest.mark.integration

CALLS = []
IDS = {}


def fake_hook(db, tenant_schema):
    """Object IDS['a'] needs x.view, IDS['b'] needs y.view."""
    CALLS.append(tenant_schema)
    return sa.select(sa.literal(IDS["a"]).label("entity_id"), sa.literal("x.view").label("permesso")).union_all(
        sa.select(sa.literal(IDS["b"]), sa.literal("y.view"))
    )


def _user(*perms):
    return User(id=1, username="t", is_superuser=False, is_active=True,
                roles=[Role(name="r", permissions=[Permission(name=p) for p in perms])])


@pytest.fixture
def ctx(db_session, unique_suffix, monkeypatch):
    s = unique_suffix
    tenant = db_session.query(Tenant).filter_by(schema_name=TEST_TENANT).one()
    db_session.add(TenantModule(tenant_id=tenant.id, module_id=f"m_{s}", enabled=True))
    sync_relation_types(db_session, {f"m_{s}": {"relation_types": [
        {"codice": f"inc_{s}", "nome": "Incarico", "entity_types": ["CONDOMINIO"]},
    ]}})
    soggetto = SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_FISICA, nome="Mario", cognome="Rossi")
    a = Condominio(codice=f"A-{s}", nome="A", indirizzo="Via Po 1", citta="Torino")
    b = Condominio(codice=f"B-{s}", nome="B", indirizzo="Via Po 2", citta="Torino")
    db_session.add_all([soggetto, a, b])
    db_session.flush()
    IDS.update(a=a.id, b=b.id)
    CALLS.clear()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_tenant_schema] = lambda: TEST_TENANT
    app.dependency_overrides[get_current_active_user] = lambda: _user("soggetto.view", "soggetto.edit")
    try:
        with TestClient(app) as client:
            from app.core.platform_services.relazione_service import RelazioneService
            svc = RelazioneService(db_session, TEST_TENANT, user_id=None)
            rels = {k: svc.crea(soggetto.id, f"inc_{s}", entity_type="CONDOMINIO", entity_id=IDS[k]) for k in "ab"}
            db_session.flush()
            yield client, rels, monkeypatch
    finally:
        for dep in (get_db, get_tenant_schema, get_current_active_user):
            app.dependency_overrides.pop(dep, None)


def _as(*perms):
    app.dependency_overrides[get_current_active_user] = lambda: _user(*perms)


def _register(monkeypatch):
    monkeypatch.setattr(
        object_permissions, "_manifest_hooks",
        lambda db, tenant_schema: {"CONDOMINIO": f"{__name__}:fake_hook"},
    )


def test_senza_hook_vale_permesso_oggetto(ctx):
    http, rels, _ = ctx
    res = http.get("/api/v1/relazioni/?entity_type=CONDOMINIO")
    assert {r["relazione_id"] for r in res.json()} == {rels["a"].id, rels["b"].id}
    assert object_permissions.hook_selects(app.dependency_overrides[get_db](), TEST_TENANT) == {}


def test_lista_filtrata_dall_hook_con_una_sola_chiamata(ctx):
    http, rels, monkeypatch = ctx
    _register(monkeypatch)
    _as("soggetto.view", "x.view")
    res = http.get("/api/v1/relazioni/?entity_type=CONDOMINIO")
    assert [r["relazione_id"] for r in res.json()] == [rels["a"].id]
    assert len(CALLS) == 1


def test_superuser_vede_tutto(ctx):
    http, rels, monkeypatch = ctx
    _register(monkeypatch)
    app.dependency_overrides[get_current_active_user] = lambda: User(
        id=1, username="s", is_superuser=True, is_active=True, roles=[])
    res = http.get("/api/v1/relazioni/?entity_type=CONDOMINIO")
    assert len(res.json()) == 2


def test_403_su_lettura_modifica_eliminazione(ctx):
    http, rels, monkeypatch = ctx
    _register(monkeypatch)
    _as("soggetto.view", "soggetto.edit", "x.view")
    b = rels["b"].id
    assert http.get(f"/api/v1/relazioni/{b}").status_code == 403
    assert http.put(f"/api/v1/relazioni/{b}", json={"note": "no"}).status_code == 403
    assert http.delete(f"/api/v1/relazioni/{b}").status_code == 403
    a = rels["a"].id
    assert http.get(f"/api/v1/relazioni/{a}").status_code == 200
    assert http.put(f"/api/v1/relazioni/{a}", json={"note": "ok"}).status_code == 200
    assert http.delete(f"/api/v1/relazioni/{a}").status_code == 204
