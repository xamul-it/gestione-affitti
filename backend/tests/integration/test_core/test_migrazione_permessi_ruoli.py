"""
Migration 2026112503: owner/tenant permissions of the user roles become bene
permissions (deliberate widening), idempotent.
"""
import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integration

MIGRAZIONE = Path(__file__).resolve().parents[3] / "alembic" / "versions" / "2026112503_permessi_proprietario_conduttore.py"
VECCHI = [f"{r}.{a}" for r in ("proprietario", "conduttore") for a in ("view", "create", "edit", "delete")]


@pytest.fixture(scope="module")
def migrazione():
    spec = importlib.util.spec_from_file_location("migr_permessi_2026112503", MIGRAZIONE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _permesso(db, nome):
    risorsa, azione = nome.split(".", 1)
    db.execute(text(
        "INSERT INTO public.core_permissions (name, description, resource, action) "
        "VALUES (:n, :n, :r, :a) ON CONFLICT (name) DO NOTHING"), {"n": nome, "r": risorsa, "a": azione})


def _ruolo(db, nome, permessi):
    db.execute(text("INSERT INTO public.core_roles (name, description, is_system) VALUES (:n, :n, false)"), {"n": nome})
    for p in permessi:
        _permesso(db, p)
        db.execute(text(
            "INSERT INTO public.core_role_permissions (role_id, permission_id) "
            "SELECT r.id, p.id FROM public.core_roles r, public.core_permissions p WHERE r.name = :r AND p.name = :p"
        ), {"r": nome, "p": p})


def _permessi(db, nome):
    return {r[0] for r in db.execute(text(
        "SELECT p.name FROM public.core_roles r JOIN public.core_role_permissions rp ON rp.role_id = r.id "
        "JOIN public.core_permissions p ON p.id = rp.permission_id WHERE r.name = :n"), {"n": nome})}


def test_migrazione_permessi_ruoli(db_session, migrazione, unique_suffix):
    db = db_session
    for p in VECCHI:
        _permesso(db, p)
    solo_vista = f"mig-vista-{unique_suffix}"
    gestore = f"mig-gestore-{unique_suffix}"
    estraneo = f"mig-estraneo-{unique_suffix}"
    _ruolo(db, solo_vista, ["proprietario.view", "soggetto.view"])
    _ruolo(db, gestore, ["conduttore.view", "conduttore.create", "proprietario.delete"])
    _ruolo(db, estraneo, ["soggetto.view"])

    toccati = migrazione.rimappa_permessi(db.connection())

    assert {solo_vista, gestore} <= set(toccati) and estraneo not in toccati
    assert _permessi(db, solo_vista) == {"soggetto.view", "immobile.view", "terreno.view"}
    assert _permessi(db, gestore) == {"immobile.view", "terreno.view", "immobile.edit", "terreno.edit"}
    assert _permessi(db, estraneo) == {"soggetto.view"}
    assert db.execute(text("SELECT count(*) FROM public.core_permissions WHERE name = ANY(:n)"),
                      {"n": VECCHI}).scalar() == 0

    # Second run: nothing left to remap, nothing changes.
    prima = (_permessi(db, solo_vista), _permessi(db, gestore), _permessi(db, estraneo))
    assert migrazione.rimappa_permessi(db.connection()) == []
    assert (_permessi(db, solo_vista), _permessi(db, gestore), _permessi(db, estraneo)) == prima
