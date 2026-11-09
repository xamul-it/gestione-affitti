"""
Every /unita-immobiliari route requires the matching immobile.* permission:
a user without it gets 403, a user with only that permission gets past the check.
"""
import pytest
from fastapi.testclient import TestClient

from app.core.auth.dependencies import get_current_active_user
from app.core.auth.models import Permission, Role, User
from app.core.database import get_db
from app.main import app

pytestmark = pytest.mark.integration

BASE = "/api/v1/unita-immobiliari"
MISSING = 999999999

ROUTES = [
    ("get", f"{BASE}/", None, "immobile.view"),
    ("get", f"{BASE}/{MISSING}", None, "immobile.view"),
    ("get", f"{BASE}/{MISSING}/variazioni-catastali", None, "immobile.view"),
    ("post", f"{BASE}/", {}, "immobile.create"),
    ("put", f"{BASE}/{MISSING}", {}, "immobile.edit"),
    ("delete", f"{BASE}/{MISSING}", None, "immobile.delete"),
]


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


def _call(http, method, url, body):
    return http.request(method, url, json=body) if body is not None else http.request(method, url)


@pytest.mark.parametrize("method,url,body,perm", ROUTES)
def test_without_permission_forbidden(http, method, url, body, perm):
    others = {"immobile.view", "immobile.create", "immobile.edit", "immobile.delete"} - {perm}
    app.dependency_overrides[get_current_active_user] = lambda: _user(*others)
    assert _call(http, method, url, body).status_code == 403


@pytest.mark.parametrize("method,url,body,perm", ROUTES)
def test_with_permission_allowed(http, method, url, body, perm):
    app.dependency_overrides[get_current_active_user] = lambda: _user(perm)
    assert _call(http, method, url, body).status_code != 403
