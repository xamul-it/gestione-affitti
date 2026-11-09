"""
Sync of the document types declared by the modules (manifest "document_types")
into public.core_tipi_documento, the table every tenant reads.

The manifest is the single source (spec
docs/superpowers/specs/2026-11-09-tipologie-documentali-moduli-design.md).
The sync runs when a module is registered/installed (partial: only that
module) and on every scripts/sync_modules.py run, i.e. every promote
(complete: all registered modules) - never at app start.

Never deletes: documents reference the rows by id. A type that no manifest
declares any more is only deactivated. Tenant overrides
(core_tipi_documento_overrides) are not touched and win in apply_override().
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.platform.models import TipoDocumento
from app.core.platform_services.document_type_registry import DocumentTypeDefinition

logger = logging.getLogger(__name__)

# Fields owned by the manifest: overwritten on every sync.
_MANIFEST_FIELDS = (
    "nome", "descrizione", "categoria", "modulo", "entity_types", "regime", "sottotipi",
    "scadenza", "promemoria_giorni", "form", "parsing_service", "parsing_config", "richiede_scadenza",
)


@dataclass
class SyncReport:
    creati: List[str] = field(default_factory=list)
    aggiornati: List[str] = field(default_factory=list)
    disattivati: List[str] = field(default_factory=list)
    errori: List[str] = field(default_factory=list)


def _definitions(manifests: Dict[str, dict]) -> Tuple[Dict[str, DocumentTypeDefinition], List[str]]:
    defs: Dict[str, DocumentTypeDefinition] = {}
    errori: List[str] = []
    for module_name, manifest in manifests.items():
        for entry in (manifest or {}).get("document_types") or []:
            codice = entry.get("codice", "?")
            try:
                d = DocumentTypeDefinition(
                    codice=entry["codice"],
                    nome=entry["nome"],
                    categoria=entry.get("categoria", "generic"),
                    modulo_origine=module_name,
                    richiede_scadenza=entry.get("richiede_scadenza", False),
                    parsing_service=entry.get("parsing_service"),
                    parsing_config=entry.get("parsing_config") or {},
                    descrizione=entry.get("descrizione"),
                    entity_types=entry.get("entity_types"),
                    regime=entry.get("regime", "CUMULATIVO"),
                    sottotipi=entry.get("sottotipi"),
                    scadenza=entry.get("scadenza"),
                    promemoria_giorni=entry.get("promemoria_giorni"),
                    form=entry.get("form"),
                )
            except (KeyError, ValueError) as exc:
                errori.append(f"{module_name}.{codice}: {exc}")
                continue
            if d.codice in defs:
                errori.append(
                    f"{d.codice}: dichiarato da {defs[d.codice].modulo_origine} e da {module_name}, "
                    f"vale {defs[d.codice].modulo_origine}"
                )
                continue
            defs[d.codice] = d
    return defs, errori


def _values(d: DocumentTypeDefinition) -> dict:
    return {
        "nome": d.nome,
        "descrizione": d.descrizione,
        "categoria": d.categoria,
        "modulo": d.modulo_origine,
        "entity_types": d.entity_types,
        "regime": d.regime,
        "sottotipi": d.sottotipi,
        "scadenza": d.scadenza,
        "promemoria_giorni": d.promemoria_giorni,
        "form": d.form,
        "parsing_service": d.parsing_service,
        "parsing_config": d.parsing_config or None,
        "richiede_scadenza": bool(d.richiede_scadenza),
    }


def sync_document_types(db: Session, manifests: Dict[str, dict], complete: bool = False) -> SyncReport:
    """
    Upsert the types declared in `manifests` ({module_name: manifest}).

    Deactivation of types no longer declared: only rows owned by a module in
    `manifests`; with complete=True (all registered modules passed) also rows
    without an owner module (legacy seeds). Flushes, does not commit.
    """
    defs, errori = _definitions(manifests)
    report = SyncReport(errori=errori)
    for e in errori:
        logger.warning("Tipologie documentali: %s", e)

    existing = {t.codice: t for t in db.query(TipoDocumento).all()}
    for codice, d in defs.items():
        values = _values(d)
        row = existing.get(codice)
        if row is None:
            db.add(TipoDocumento(codice=codice, attivo=True, **values))
            report.creati.append(codice)
            continue
        changed = False
        for name in _MANIFEST_FIELDS:
            if getattr(row, name) != values[name]:
                setattr(row, name, values[name])
                changed = True
        if not row.attivo:
            row.attivo = True
            changed = True
        if changed:
            report.aggiornati.append(codice)

    for codice, row in existing.items():
        if codice in defs or not row.attivo:
            continue
        owned = row.modulo in manifests if row.modulo else complete
        if owned:
            row.attivo = False
            report.disattivati.append(codice)

    db.flush()
    return report


def apply_override(tipo: TipoDocumento, override) -> Optional[dict]:
    """Type as seen by a tenant: override fields win; None if the tenant deleted it."""
    if override is not None and override.is_deleted:
        return None

    def pick(name):
        value = getattr(override, name, None) if override is not None else None
        return value if value is not None else getattr(tipo, name)

    return {
        "id": tipo.id,
        "codice": pick("codice"),
        "nome": pick("nome"),
        "descrizione": pick("descrizione"),
        "categoria": pick("categoria"),
        "richiede_scadenza": pick("richiede_scadenza"),
        "attivo": pick("attivo"),
        "modulo": tipo.modulo,
        "entity_types": tipo.entity_types,
        "regime": tipo.regime,
        "sottotipi": tipo.sottotipi,
        "scadenza": tipo.scadenza,
        "promemoria_giorni": tipo.promemoria_giorni,
        "form": tipo.form,
        "parsing_service": tipo.parsing_service,
        "parsing_config": tipo.parsing_config,
        "parsing_callback_url": tipo.parsing_callback_url,
    }
