"""Remap the owner/tenant permissions of the user roles to the bene permissions.

Owners and tenants of a bene are core relations now, so the permissions
proprietario.* and conduttore.* are gone. A role that had proprietario.view or
conduttore.view gets immobile.view and terreno.view; a role that had one of the
corresponding create/edit/delete gets immobile.edit and terreno.edit. Then the
eight old permissions are removed.

DELIBERATE WIDENING: a role that saw only the owners (or only the tenants) now
sees every bene and their relations. Accepted: the only real user already has
the permissions on the beni. Before a release, count the production roles that
hold the old permissions.

Idempotent: a second run finds no old permission and changes nothing. Prints
the roles it touched.

Revision ID: 2026112503
Revises: 2026112502
Create Date: 2026-11-25
"""
from typing import List

from alembic import op
import sqlalchemy as sa

revision = "2026112503"
down_revision = "2026112502"
branch_labels = None
depends_on = None

target_schema = "public"

_VECCHI = [f"{r}.{a}" for r in ("proprietario", "conduttore") for a in ("view", "create", "edit", "delete")]
_VISTA = ("proprietario.view", "conduttore.view")
_SCRITTURA = tuple(n for n in _VECCHI if n not in _VISTA)
_NUOVI_VISTA = ("immobile.view", "terreno.view")
_NUOVI_SCRITTURA = ("immobile.edit", "terreno.edit")


def _ruoli_con(conn, nomi) -> List[str]:
    return [r[0] for r in conn.execute(sa.text(
        "SELECT DISTINCT r.name FROM public.core_roles r "
        "JOIN public.core_role_permissions rp ON rp.role_id = r.id "
        "JOIN public.core_permissions p ON p.id = rp.permission_id "
        "WHERE p.name = ANY(:nomi) ORDER BY r.name"), {"nomi": list(nomi)})]


def _concedi(conn, ruolo: str, permessi) -> None:
    for nome in permessi:
        risorsa, azione = nome.split(".", 1)
        conn.execute(sa.text(
            "INSERT INTO public.core_permissions (name, description, resource, action) "
            "VALUES (:n, :n, :r, :a) ON CONFLICT (name) DO NOTHING"), {"n": nome, "r": risorsa, "a": azione})
        conn.execute(sa.text(
            "INSERT INTO public.core_role_permissions (role_id, permission_id) "
            "SELECT r.id, p.id FROM public.core_roles r, public.core_permissions p "
            "WHERE r.name = :ruolo AND p.name = :n ON CONFLICT DO NOTHING"), {"ruolo": ruolo, "n": nome})


def rimappa_permessi(conn) -> List[str]:
    """Remap and remove the old permissions; returns the touched roles."""
    ruoli_vista = _ruoli_con(conn, _VISTA)
    ruoli_scrittura = _ruoli_con(conn, _SCRITTURA)
    for ruolo in ruoli_vista:
        _concedi(conn, ruolo, _NUOVI_VISTA)
    for ruolo in ruoli_scrittura:
        _concedi(conn, ruolo, _NUOVI_SCRITTURA)
    conn.execute(sa.text(
        "DELETE FROM public.core_role_permissions WHERE permission_id IN "
        "(SELECT id FROM public.core_permissions WHERE name = ANY(:nomi))"), {"nomi": _VECCHI})
    conn.execute(sa.text("DELETE FROM public.core_permissions WHERE name = ANY(:nomi)"), {"nomi": _VECCHI})
    return sorted(set(ruoli_vista) | set(ruoli_scrittura))


def upgrade() -> None:
    conn = op.get_bind()
    # The op.* gate does not cover conn.execute: run in the public pass only.
    if conn.execute(sa.text("SELECT current_schema()")).scalar() != "public":
        return
    toccati = rimappa_permessi(conn)
    print(f"[2026112503] roles remapped to immobile/terreno permissions: {toccati or 'none'}")


def downgrade() -> None:
    # The old permissions are not restored: the data they protected is gone.
    pass
