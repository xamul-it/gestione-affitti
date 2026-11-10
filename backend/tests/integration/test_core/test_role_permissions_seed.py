"""
Default roles and module permissions:
- startup (init_auth_data) only adds what is missing: it never strips the
  module permissions sync_module_permissions granted (they used to vanish at
  every backend start);
- module permissions go to the admin roles (all), Manager (all but delete and
  admin) and Viewer (view/read only).
"""
import pytest

from app.core.auth.init_data import init_auth_data
from app.core.auth.models import Role
from app.core.auth.seed_platform_permissions import sync_module_permissions

pytestmark = pytest.mark.integration

MANIFEST = {"permissions": [
    {"name": "zz_test.view"}, {"name": "zz_test.create"}, {"name": "zz_test.edit"},
    {"name": "zz_test.delete"}, {"name": "zz_test.read"}, {"name": "zz_test.admin"},
    {"name": "zz_test.audit.view"},
]}


def _perms(db, role):
    return {p.name for p in db.query(Role).filter_by(name=role).one().permissions if p.name.startswith("zz_test.")}


def test_avvio_non_toglie_i_permessi_dei_moduli(db_session):
    init_auth_data(db_session)
    sync_module_permissions(db_session, MANIFEST)
    assert "zz_test.delete" in _perms(db_session, "Admin")

    init_auth_data(db_session)

    assert "zz_test.delete" in _perms(db_session, "Admin")


def test_manager_senza_delete_ne_admin(db_session):
    init_auth_data(db_session)
    sync_module_permissions(db_session, MANIFEST)
    assert _perms(db_session, "Manager") == {
        "zz_test.view", "zz_test.create", "zz_test.edit", "zz_test.read", "zz_test.audit.view",
    }


def test_viewer_solo_lettura(db_session):
    init_auth_data(db_session)
    sync_module_permissions(db_session, MANIFEST)
    assert _perms(db_session, "Viewer") == {"zz_test.view", "zz_test.read", "zz_test.audit.view"}
