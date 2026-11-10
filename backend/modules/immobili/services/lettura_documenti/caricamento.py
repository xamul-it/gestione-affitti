"""
Single upload point: analyse a file (type, unit, data, differences) and,
after the user's confirmation, save it on the unit.

Values read from the document always come from the file, re-read server side
at confirmation; the client only contributes the type and unit it chose,
fields the document doesn't have (e.g. the APE class drawn as a graphic) and
the differences it selected.
"""
import hashlib
import io
import logging
from types import SimpleNamespace
from datetime import date, timedelta
from typing import Optional, Set

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.file_storage import file_storage
from app.core.platform.models import DocumentJob, Documento, EntityType, JobStatus, StatoScadenza, TipoDocumento
from app.core.platform_services.document_parsing_service import DocumentParsingService
from app.core.platform_services.scadenze_collegate import chiudi
from app.core.platform_services.documento_service import DocumentoService, FileInput

from ...models import UnitaImmobiliare
from ...schemas.caricamento_documenti import AnalisiDocumento, ConfermaDocumento
from .. import upload_temporanei
from ..variazioni_catastali import registra_variazioni
from ..visura import VisuraFormatError
from ..visura.text import pdf_to_text
from .abbinamento import CAMPI_CONFRONTO, abbina_unita, differenze
from .lettori import CLASSI_ENERGETICHE, LETTORI, normalizza, riconosci_tipo, spec_per_codice
from .motore import applica

logger = logging.getLogger(__name__)

PERMESSI_VISURA = ("documenti.write", "soggetto.create", "soggetto.edit")
MSG_TIPO = "Tipo di documento non riconosciuto: sceglilo"
MSG_IMMOBILE = "Immobile non trovato dai dati del documento: sceglilo"
MSG_VISURA_PERMESSO = "Serve il permesso di import visure"
MSG_APE_VECCHIO = "APE più vecchio di quello in vigore: verrà archiviato come storico"
MSG_SCADUTO = "Caricamento scaduto o non trovato, ricarica il documento"
MSG_CLASSE = "Indica la classe energetica (A4…G)"
MSG_DUPLICATO = "Documento già presente su questo immobile"
MSG_OCR_FALLITO = "Lettura non riuscita: scegli tipo e immobile"
SERVIZIO_OCR = "ocr_testo"
MINUTI_MAX_LETTURA = 30  # a job with no callback after this is treated as failed
TIPO_JOB_OCR = "immobili.ALTRO_IMMOBILE"  # placeholder: the real type is known only after reading
CAMPI_DATI_APE = ("classe", "ep_gl_nren", "codice_identificativo", "tecnico_id", "decaduto_il")


class CaricamentoError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _testo(contenuto: bytes) -> Optional[str]:
    try:
        return pdf_to_text(contenuto)
    except VisuraFormatError:
        return None


def _tipi_immobile(db: Session, tenant_schema: str) -> Set[str]:
    return {t["codice"] for t in DocumentoService(db, tenant_schema, None).tipi_per_entita(EntityType.IMMOBILE)}


def _hash(contenuto: bytes) -> str:
    return hashlib.sha256(contenuto).hexdigest()


def _hash_documenti(db: Session, tenant_schema: str, unita_id: int) -> Set[str]:
    out = set()
    docs = db.query(Documento).filter(Documento.entity_type == EntityType.IMMOBILE, Documento.entity_id == unita_id)
    for d in docs:
        paths = [f.file_path for f in d.files] or ([d.file_path] if d.file_path else [])
        for p in paths:
            try:
                out.add(_hash(file_storage.get_file_path(p, tenant_schema).read_bytes()))
            except OSError:
                logger.warning("File del documento %s non leggibile: %s", d.id, p)
    return out


def _ape_corrente(db: Session, unita_id: int) -> Optional[Documento]:
    return (db.query(Documento).join(TipoDocumento, TipoDocumento.id == Documento.tipo_documento_id)
            .filter(TipoDocumento.codice == "APE", Documento.entity_type == EntityType.IMMOBILE,
                    Documento.entity_id == unita_id, Documento.stato == "CORRENTE").first())


def campi_letti(tipo_codice: str, testo: Optional[str]) -> dict:
    spec = spec_per_codice(tipo_codice)
    if spec is None or not testo:
        return {}
    return normalizza(tipo_codice, applica(spec, testo).campi)


def analizza_campi(db: Session, tenant_schema: str, permessi: Set[str], *, token: str, nome_file: str,
                   contenuto: bytes, tipo_codice: Optional[str], dati: dict,
                   unita_id: Optional[int] = None) -> AnalisiDocumento:
    """Decide the outcome once the type (if any) and the read data are known."""
    base = dict(upload_token=token, nome_file=nome_file, tipo_codice=tipo_codice, dati=dati)
    if not tipo_codice:
        return AnalisiDocumento(esito="scegli_tipo", messaggio=MSG_TIPO, **base)
    spec = spec_per_codice(tipo_codice)
    if spec is not None and spec.scarto:
        return AnalisiDocumento(esito="scartato", messaggio=spec.scarto, **base)
    if tipo_codice == "VISURA_CATASTALE":
        if "*" not in permessi and not all(p in permessi for p in PERMESSI_VISURA):
            return AnalisiDocumento(esito="scartato", messaggio=MSG_VISURA_PERMESSO, **base)
        return AnalisiDocumento(esito="visura", **base)
    if tipo_codice not in _tipi_immobile(db, tenant_schema):
        return AnalisiDocumento(esito="scegli_tipo", messaggio=MSG_TIPO, **{**base, "tipo_codice": None})

    candidati = []
    if unita_id is None:
        abbinamento = abbina_unita(db, dati)
        unita_id, candidati = abbinamento.unita_id, abbinamento.candidati
    unita = db.get(UnitaImmobiliare, unita_id) if unita_id else None
    if unita is None:
        return AnalisiDocumento(esito="scegli_immobile", messaggio=MSG_IMMOBILE, candidati=candidati, **base)

    avvisi = []
    if tipo_codice == "APE" and dati.get("data_emissione"):
        corrente = _ape_corrente(db, unita.id)
        if corrente and corrente.data_riferimento and corrente.data_riferimento > date.fromisoformat(dati["data_emissione"]):
            avvisi.append(MSG_APE_VECCHIO)
    esito = "gia_presente" if _hash(contenuto) in _hash_documenti(db, tenant_schema, unita.id) else "pronto"
    return AnalisiDocumento(esito=esito, messaggio=MSG_DUPLICATO if esito == "gia_presente" else None,
                            unita_id=unita.id, differenze=differenze(unita, dati), avvisi=avvisi, **base)


def _avvia_ocr(db: Session, tenant_schema: str, user_id: int, contenuto: bytes, nome_file: str,
               mime_type: Optional[str]) -> DocumentJob:
    """Send a scan to the external OCR text mode with the specs of every immobili type."""
    upload = SimpleNamespace(file=io.BytesIO(contenuto), filename=nome_file, content_type=mime_type)
    return DocumentParsingService(db, tenant_schema).upload_and_parse(
        upload, TIPO_JOB_OCR, user_id=user_id, parsing_service_override=SERVIZIO_OCR,
        parsing_config_override={
            "modalita": "testo",
            "tipi": [spec.to_dict() for spec in LETTORI],
            "titolo_attivita": f"Documento immobile letto: {nome_file} — completa il caricamento",
        })


def analizza_contenuto(db: Session, tenant_schema: str, permessi: Set[str], user_id: int, contenuto: bytes,
                       nome_file: str, mime_type: Optional[str]) -> AnalisiDocumento:
    token = upload_temporanei.salva(tenant_schema, contenuto, nome_file, mime_type)
    testo = _testo(contenuto)
    if testo is None:
        job = _avvia_ocr(db, tenant_schema, user_id, contenuto, nome_file, mime_type)
        upload_temporanei.scrivi_meta(tenant_schema, token, {"nome_file": nome_file, "mime_type": mime_type,
                                                             "job_uuid": job.job_uuid})
        if job.status == JobStatus.FAILED:
            return AnalisiDocumento(upload_token=token, nome_file=nome_file, esito="errore",
                                    messaggio=MSG_OCR_FALLITO, job_uuid=job.job_uuid)
        return AnalisiDocumento(upload_token=token, nome_file=nome_file, esito="in_lettura", job_uuid=job.job_uuid)
    r = riconosci_tipo(testo)
    tipo = r.codice if r else None
    return analizza_campi(db, tenant_schema, permessi, token=token, nome_file=nome_file, contenuto=contenuto,
                          tipo_codice=tipo, dati=normalizza(tipo, r.campi) if r else {})


def _risultato_ocr(result: dict) -> dict:
    """Service response -> {codice: {campo: valore}} plus the first recognised type."""
    ocr = {}
    tipo = None
    for t in (result or {}).get("tipi") or []:
        codice = t.get("codice")
        if not codice:
            continue
        ocr[codice] = {k: (v or {}).get("valore") for k, v in (t.get("campi") or {}).items() if (v or {}).get("valore")}
        if tipo is None and t.get("riconosciuto"):
            tipo = codice
    return {"ocr": ocr, "tipo_ocr": tipo}


def stato_analisi(db: Session, tenant_schema: str, permessi: Set[str], token: str) -> AnalisiDocumento:
    """Analysis of an upload read by OCR: still reading, failed, or the result as for a native-text PDF."""
    contenuto, meta = _upload(tenant_schema, token)
    nome_file = meta.get("nome_file") or "documento"
    job_uuid = meta.get("job_uuid")
    if not job_uuid:
        return rianalizza(db, tenant_schema, permessi, token, None, None)
    if "ocr" not in meta:
        job = db.query(DocumentJob).filter(DocumentJob.job_uuid == job_uuid,
                                           DocumentJob.tenant_schema == tenant_schema).first()
        if job is None or job.status in (JobStatus.FAILED, JobStatus.TIMEOUT, JobStatus.CANCELLED):
            return AnalisiDocumento(upload_token=token, nome_file=nome_file, esito="errore",
                                    messaggio=MSG_OCR_FALLITO, job_uuid=job_uuid)
        if job.status != JobStatus.COMPLETED:
            # Ages are computed by the DB: created_at is its naive now().
            scaduto = db.query(DocumentJob.id).filter(
                DocumentJob.id == job.id,
                DocumentJob.created_at < func.now() - timedelta(minutes=MINUTI_MAX_LETTURA)).first()
            if scaduto:
                return AnalisiDocumento(upload_token=token, nome_file=nome_file, esito="errore",
                                        messaggio=MSG_OCR_FALLITO, job_uuid=job_uuid)
            return AnalisiDocumento(upload_token=token, nome_file=nome_file, esito="in_lettura", job_uuid=job_uuid)
        meta.update(_risultato_ocr(job.parsing_result))
        upload_temporanei.scrivi_meta(tenant_schema, token, meta)
    analisi = rianalizza(db, tenant_schema, permessi, token, None, None)
    analisi.job_uuid = job_uuid
    return analisi


def _upload(tenant_schema: str, token: str):
    letto = upload_temporanei.leggi(tenant_schema, token)
    if letto is None:
        raise CaricamentoError(404, MSG_SCADUTO)
    return letto


def dati_dal_file(tenant_schema: str, tipo_codice: str, contenuto: bytes, meta: dict) -> dict:
    """Read data for the type, from the file (native text) or from the OCR result kept in the upload."""
    if tipo_codice in (meta.get("ocr") or {}):
        return normalizza(tipo_codice, meta["ocr"][tipo_codice])
    return campi_letti(tipo_codice, _testo(contenuto))


def rianalizza(db: Session, tenant_schema: str, permessi: Set[str], token: str,
               tipo_codice: Optional[str], unita_id: Optional[int]) -> AnalisiDocumento:
    contenuto, meta = _upload(tenant_schema, token)
    if tipo_codice is None:
        tipo_codice = meta.get("tipo_ocr")
    dati = dati_dal_file(tenant_schema, tipo_codice, contenuto, meta) if tipo_codice else {}
    return analizza_campi(db, tenant_schema, permessi, token=token, nome_file=meta.get("nome_file") or "documento",
                          contenuto=contenuto, tipo_codice=tipo_codice, dati=dati, unita_id=unita_id)


def conferma(db: Session, tenant_schema: str, user_id: int, body: ConfermaDocumento) -> Documento:
    contenuto, meta = _upload(tenant_schema, body.upload_token)
    if body.tipo_codice not in _tipi_immobile(db, tenant_schema) or body.tipo_codice == "VISURA_CATASTALE":
        raise CaricamentoError(422, "Tipo di documento non valido per un immobile")
    unita = db.get(UnitaImmobiliare, body.unita_id)
    if unita is None:
        raise CaricamentoError(404, "Immobile non trovato")
    if not body.forza_duplicato and _hash(contenuto) in _hash_documenti(db, tenant_schema, unita.id):
        raise CaricamentoError(409, MSG_DUPLICATO)

    letti = dati_dal_file(tenant_schema, body.tipo_codice, contenuto, meta)
    dati_doc = None
    data_riferimento = None
    descrizione = None
    if body.tipo_codice == "APE":
        # Read values win; the client only fills what the document doesn't have.
        dati_doc = {k: v for k, v in {**body.dati, **letti}.items() if k in CAMPI_DATI_APE and v not in (None, "")}
        if dati_doc.get("classe") not in CLASSI_ENERGETICHE:
            raise CaricamentoError(422, MSG_CLASSE)
        data_riferimento = date.fromisoformat(letti["data_emissione"]) if letti.get("data_emissione") else None
        descrizione = f"APE classe {dati_doc['classe']}"

    nuovi = {d.campo: letti[d.campo] for d in body.differenze
             if d.selezionato and d.campo in CAMPI_CONFRONTO and letti.get(d.campo) not in (None, "")}

    service = DocumentoService(db, tenant_schema, user_id)
    documento = service.crea(
        entity_type=EntityType.IMMOBILE, entity_id=unita.id, tipo_codice=body.tipo_codice,
        files=[FileInput(contenuto, meta.get("nome_file") or "documento", meta.get("mime_type"))],
        data_riferimento=data_riferimento, dati=dati_doc, descrizione=descrizione,
    )
    try:
        if nuovi:
            registra_variazioni(db, unita, nuovi, origine="DOCUMENTO", documento_id=documento.id,
                                data_riferimento=documento.data_riferimento, utente_id=user_id)
            for campo, valore in nuovi.items():
                setattr(unita, campo, valore)
        if meta.get("job_uuid"):
            job = db.query(DocumentJob).filter(DocumentJob.job_uuid == meta["job_uuid"],
                                               DocumentJob.tenant_schema == tenant_schema).first()
            if job is not None:
                chiudi(db, job.scadenza_id, StatoScadenza.COMPLETATA,
                       f"Documento caricato sull'immobile {unita.id}", user_id)
        db.flush()
    except Exception:
        # The DB rolls back with the caller; the files crea() saved must go too.
        elimina_file(db, tenant_schema, percorsi_file(documento))
        raise
    return documento


def percorsi_file(documento: Documento) -> list:
    return [f.file_path for f in documento.files]


def elimina_file(db: Session, tenant_schema: str, percorsi: list) -> None:
    DocumentoService(db, tenant_schema, None).elimina_file(percorsi)
