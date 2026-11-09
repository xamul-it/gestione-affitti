"""
Every route of the immobili module requires a permission: a user lacking it
gets 403, a user holding only that permission gets past the check.
The expected permission is derived from the router prefix and HTTP method.
"""
import re

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.core.auth.dependencies import get_current_active_user
from app.core.auth.models import Permission, Role, User
from app.core.database import get_db
from app.main import app

pytestmark = pytest.mark.integration

API = "/api/v1"
ACTION = {"GET": "view", "POST": "create", "PUT": "edit", "DELETE": "delete"}

# prefix -> resource whose <resource>.<action> guards the route
RESOURCES = {
    "/unita-immobiliari": "immobile",
    "/condomini": "condominio",
    "/tabelle-millesimali": "condominio",
    "/millesimi-immobile": "condominio",
    "/conduttori": "conduttore",
    "/assegnazioni-conduttore": "conduttore",
    "/proprietari": "proprietario",
    "/diritti-immobile": "proprietario",
    "/terreni": "terreno",
}
# shared domain tables in public: read by module users, written by platform admins
DOMAIN = {"/categorie-catastali": "immobile.view", "/tipologie-terreno": "terreno.view"}
SPECIAL = {("POST", "/terreni/{terreno_id}/restore"): "terreno.edit"}
# already guarded by their own permission scheme, covered by their tests
SKIP = ("/unita-immobiliari/import-visura", "/certificati-energetici", "/spese-ricorrenti")

ALL_PERMS = {f"{r}.{a}" for r in set(RESOURCES.values()) for a in ACTION.values()} | {"platform.admin"}


def _expected(method, path):
    rel = path[len(API):]
    if (method, rel) in SPECIAL:
        return SPECIAL[(method, rel)]
    for prefix, read_perm in DOMAIN.items():
        if rel.startswith(prefix):
            return read_perm if method == "GET" else "platform.admin"
    for prefix, resource in sorted(RESOURCES.items(), key=lambda kv: -len(kv[0])):
        if rel == prefix or rel.startswith(prefix + "/"):
            return f"{resource}.{ACTION[method]}"
    return None


def _cases():
    cases = []
    for route in app.routes:
        if not isinstance(route, APIRoute) or not route.path.startswith(API):
            continue
        rel = route.path[len(API):]
        if rel.startswith(SKIP):
            continue
        for method in route.methods & set(ACTION):
            perm = _expected(method, route.path)
            if perm:
                url = re.sub(r"\{codice\}", "ZZZ", route.path)
                url = re.sub(r"\{[^}]+\}", "999999999", url)
                cases.append(pytest.param(method, url, perm, id=f"{method} {rel}"))
    return cases


CASES = _cases()


def test_all_module_prefixes_found():
    paths = {c.values[1] for c in CASES}
    for prefix in list(RESOURCES) + list(DOMAIN):
        assert any(p.startswith(API + prefix) for p in paths), prefix


def _user(*perms):
    return User(id=1, username="t", is_superuser=False, is_active=True,
                roles=[Role(name="r", permissions=[Permission(name=p) for p in perms])])


@pytest.fixture
def http(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_active_user, None)


def _call(http, method, url):
    return http.request(method, url, json={} if method in ("POST", "PUT") else None)


@pytest.mark.parametrize("method,url,perm", CASES)
def test_without_permission_forbidden(http, method, url, perm):
    app.dependency_overrides[get_current_active_user] = lambda: _user(*(ALL_PERMS - {perm}))
    assert _call(http, method, url).status_code == 403


@pytest.mark.parametrize("method,url,perm", CASES)
def test_with_permission_allowed(http, method, url, perm):
    app.dependency_overrides[get_current_active_user] = lambda: _user(perm)
    assert _call(http, method, url).status_code != 403
