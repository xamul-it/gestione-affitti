"""
Sync of the relation types declared by the modules (manifest
"relation_types") into public.core_ruoli_disponibili, the shared catalog.

Runs when a module is installed (partial: only that module) and on every
scripts/sync_modules.py run (complete: all registered modules). Never deletes:
relations reference the rows. Undeclared rows are only deactivated; rows of
modules that still register roles through `endpoints.register_roles`
(gestione_pec) are left alone.
"""
import logging
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from app.core.models import RuoloDisponibile
from app.core.platform_services.document_type_sync import SyncReport
from app.core.platform_services.relation_type_registry import RelationTypeDefinition

logger = logging.getLogger(__name__)

# Modules whose catalog rows are written by their own register_roles hook.
REGISTER_ROLES_MODULES = ("gestione_pec",)

_FIELDS = (
    "nome_display", "descrizione", "entity_types", "fonte", "provider", "scadenza",
    "promemoria_giorni", "sottotipi_fonte", "unico_per_oggetto", "permesso_oggetto",
)


def _definitions(manifests: Dict[str, dict]) -> Tuple[Dict[tuple, RelationTypeDefinition], List[str]]:
    defs: Dict[tuple, RelationTypeDefinition] = {}
    errori: List[str] = []
    for module_name, manifest in manifests.items():
        for entry in (manifest or {}).get("relation_types") or []:
            try:
                d = RelationTypeDefinition(modulo=module_name, **entry)
            except (TypeError, ValueError) as exc:
                errori.append(f"{module_name}.{entry.get('codice', '?')}: {exc}")
                continue
            defs[(d.codice, module_name)] = d
    return defs, errori


def _values(d: RelationTypeDefinition) -> dict:
    return {
        "nome_display": d.nome,
        "descrizione": d.descrizione,
        "entity_types": d.entity_types,
        "fonte": d.fonte,
        "provider": d.provider,
        "scadenza": d.scadenza,
        "promemoria_giorni": d.promemoria_giorni,
        "sottotipi_fonte": d.sottotipi_fonte,
        "unico_per_oggetto": bool(d.unico_per_oggetto),
        "permesso_oggetto": d.permesso_oggetto,
    }


def sync_relation_types(db: Session, manifests: Dict[str, dict], complete: bool = False) -> SyncReport:
    """Upsert the declared types; flushes, does not commit."""
    defs, errori = _definitions(manifests)
    report = SyncReport(errori=errori)
    for e in errori:
        logger.warning("Tipi di relazione: %s", e)

    existing = {(r.codice, r.modulo_id): r for r in db.query(RuoloDisponibile).all()}
    for key, d in defs.items():
        values = _values(d)
        row = existing.get(key)
        if row is None:
            db.add(RuoloDisponibile(codice=d.codice, modulo_id=d.modulo, attivo=True, **values))
            report.creati.append(d.codice)
            continue
        changed = False
        for name in _FIELDS:
            if getattr(row, name) != values[name]:
                setattr(row, name, values[name])
                changed = True
        if not row.attivo:
            row.attivo = True
            changed = True
        if changed:
            report.aggiornati.append(d.codice)

    for key, row in existing.items():
        if key in defs or not row.attivo or row.modulo_id in REGISTER_ROLES_MODULES:
            continue
        if row.modulo_id in manifests or complete:
            row.attivo = False
            report.disattivati.append(row.codice)

    db.flush()
    return report
