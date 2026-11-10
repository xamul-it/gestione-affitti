"""
Role relations and the tenant module lifecycle.

- A relation type belongs to a module (core_ruoli_disponibili.modulo_id):
  while that module is not enabled in the tenant, its relations are hidden
  and can't be written (relazioni_query / RelazioneService).
- Disabling or uninstalling a module (tables kept) cancels the scadenze of
  its core relations; enabling it again reopens them. The relations stay.
- Dropping a module's tables deletes its core relations (their scadenze are
  cancelled): their objects are gone.
- A module can't be disabled or uninstalled while an enabled module of the
  tenant depends on it.

Flushes, never commits: the caller owns the transaction.
"""
from contextlib import contextmanager
from typing import List, Optional, Set

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.models import RuoloDisponibile
from app.core.models.tenant import Tenant, TenantModule
from app.core.platform.models import Relazione, StatoScadenza


def moduli_attivi(db: Session, tenant_schema: Optional[str]) -> Optional[Set[str]]:
    """Enabled modules of the tenant; None when unknown (no filter)."""
    if not tenant_schema:
        return None
    rows = (db.query(TenantModule.module_id)
            .join(Tenant, Tenant.id == TenantModule.tenant_id)
            .filter(Tenant.schema_name == tenant_schema, TenantModule.enabled.is_(True)).all())
    return {r[0] for r in rows} or None


def verifica_modulo_attivo(db: Session, tenant_schema: Optional[str], tipo: RuoloDisponibile) -> None:
    attivi = moduli_attivi(db, tenant_schema)
    if attivi is not None and tipo.modulo_id and tipo.modulo_id not in attivi:
        raise ValueError(f"Il modulo {tipo.modulo_id} non è attivo: '{tipo.nome_display}' non è modificabile")


def moduli_dipendenti(db: Session, tenant_id: int, module_id: str) -> List[str]:
    """Enabled modules of the tenant whose manifest depends on module_id."""
    from app.core.module_system.models import Module

    rows = (db.query(Module)
            .join(TenantModule, TenantModule.module_id == Module.technical_name)
            .filter(TenantModule.tenant_id == tenant_id, TenantModule.enabled.is_(True),
                    Module.technical_name != module_id).all())
    return sorted(m.technical_name for m in rows
                  if module_id in ((m.manifest or {}).get("dependencies") or []))


def verifica_dipendenti(db: Session, tenant_id: int, module_id: str) -> None:
    dipendenti = moduli_dipendenti(db, tenant_id, module_id)
    if dipendenti:
        raise ValueError(
            f"Il modulo {module_id} serve a {', '.join(dipendenti)}: disattiva prima "
            f"{'quello' if len(dipendenti) == 1 else 'quelli'}"
        )


@contextmanager
def _nello_schema(db: Session, tenant_schema: str):
    """Run in the tenant schema, then restore the session's search_path."""
    precedente = db.info.get("search_path") or "public"
    db.execute(text(f"SET search_path TO {tenant_schema}, public"))
    try:
        yield
    finally:
        db.execute(text(f"SET search_path TO {precedente}"))


def _relazioni(db: Session, tenant_schema: str, module_id: str) -> List[Relazione]:
    if not inspect(db.get_bind()).has_table("core_relazioni", schema=tenant_schema):
        return []
    tipi = [t.id for t in db.query(RuoloDisponibile).filter(RuoloDisponibile.modulo_id == module_id)]
    if not tipi:
        return []
    return db.query(Relazione).filter(Relazione.ruolo_id.in_(tipi)).all()


def _schema(db: Session, tenant_id: int) -> Optional[str]:
    tenant = db.get(Tenant, tenant_id)
    return tenant.schema_name if tenant else None


def sospendi(db: Session, tenant_id: int, module_id: str) -> int:
    """Cancel the open scadenze of the module's core relations; returns how many relations."""
    from app.core.platform_services.scadenze_collegate import chiudi, utente_sistema

    schema = _schema(db, tenant_id)
    if not schema:
        return 0
    with _nello_schema(db, schema):
        rels = [r for r in _relazioni(db, schema, module_id) if r.scadenza_id]
        user = utente_sistema(db) if rels else None
        for rel in rels:
            chiudi(db, rel.scadenza_id, StatoScadenza.CANCELLATA,
                   f"Modulo {module_id} disattivato: relazione {rel.id} sospesa", user)
            rel.scadenza_id = None
        db.flush()
    return len(rels)


def riattiva(db: Session, tenant_id: int, module_id: str) -> int:
    """Reopen the scadenze of the module's current core relations; returns how many relations."""
    from app.core.platform_services.relazione_service import RelazioneService, e_corrente

    schema = _schema(db, tenant_id)
    if not schema:
        return 0
    with _nello_schema(db, schema):
        # Only relations suspended by sospendi() (no linked scadenza): this also
        # runs on every release, and must not reopen scadenze closed by hand.
        rels = [r for r in _relazioni(db, schema, module_id)
                if r.scadenza_id is None and r.data_scadenza and e_corrente(r.data_fine)]
        service = RelazioneService(db, schema)
        for rel in rels:
            service._sync_scadenza(db.get(RuoloDisponibile, rel.ruolo_id), rel)
        db.flush()
    return len(rels)


def elimina(db: Session, tenant_id: int, module_id: str) -> int:
    """Delete the module's core relations (their objects are being dropped); cancels their scadenze."""
    from app.core.platform_services.relazione_service import RelazioneService

    schema = _schema(db, tenant_id)
    if not schema:
        return 0
    with _nello_schema(db, schema):
        rels = _relazioni(db, schema, module_id)
        service = RelazioneService(db, schema)
        for rel in rels:
            service.elimina(rel.id)
        db.flush()
    return len(rels)
