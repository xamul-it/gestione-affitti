"""
Energy certificates (immo_certificati_energetici, the old model) -> core
documents of type APE. Idempotent (a certificate already migrated carries its
id in dati.certificato_id) and never deletes: the old table stays read-only.
Run per tenant by the immobili post_sync hook (scripts/sync_modules.py), after
the document types have been synced.
"""
import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.file_storage import file_storage
from app.core.platform.models import Documento, DocumentoFile, EntityType, TipoDocumento
from app.core.platform.models.documento import TipoDocumentoEnum

logger = logging.getLogger(__name__)


def _file_exists(file_path: str) -> bool:
    try:
        return file_storage.get_file_path(file_path).exists() or Path(file_path).exists()
    except Exception:
        return False


def migra_ape(db: Session, tenant_schema: str) -> dict:
    report = {"letti": 0, "creati": 0, "saltati": 0, "senza_file": 0}
    if db.execute(text("SELECT to_regclass('immo_certificati_energetici')")).scalar() is None:
        return report
    tipo = db.query(TipoDocumento).filter(TipoDocumento.codice == "APE").first()
    if tipo is None:
        raise RuntimeError("Tipologia APE mancante: sincronizzare prima le tipologie documentali")

    migrati = {
        (d.dati or {}).get("certificato_id")
        for d in db.query(Documento).filter(Documento.tipo_documento_id == tipo.id).all()
    }
    rows = db.execute(text("""
        SELECT id, unita_immobiliare_id, tecnico_id, classe_energetica::text AS classe,
               indice_prestazione_energetica, data_emissione, data_scadenza, numero_protocollo,
               file_path, note
        FROM immo_certificati_energetici ORDER BY id
    """)).all()
    for r in rows:
        report["letti"] += 1
        if r.id in migrati:
            report["saltati"] += 1
            continue
        documento = Documento(
            entity_type=EntityType.IMMOBILE,
            entity_id=r.unita_immobiliare_id,
            tipo_documento=TipoDocumentoEnum.CERTIFICATO_ENERGETICO,
            tipo_documento_id=tipo.id,
            descrizione=f"APE classe {r.classe}",
            note=r.note,
            data_riferimento=r.data_emissione,
            data_scadenza=r.data_scadenza,
            stato="CORRENTE",
            dati={
                "classe": r.classe,
                "ep_gl_nren": r.indice_prestazione_energetica,
                "codice_identificativo": r.numero_protocollo,
                "tecnico_id": r.tecnico_id,
                "certificato_id": r.id,
            },
        )
        if r.file_path and _file_exists(r.file_path):
            nome = Path(r.file_path).name
            documento.nome_file, documento.file_path, documento.mime_type = nome, r.file_path, "application/pdf"
            documento.files.append(DocumentoFile(
                file_path=r.file_path, nome_file=nome, mime_type="application/pdf", ordine=1, tipo_pagina="unico",
            ))
        else:
            report["senza_file"] += 1
        db.add(documento)
        report["creati"] += 1
    db.flush()
    if report["creati"]:
        from app.core.platform_services.documento_service import DocumentoService
        service = DocumentoService(db, tenant_schema, None)
        service.allinea_storico("APE")
        service.allinea_scadenze("APE")
    return report
