"""
Single upload point, scans: files without text go to the external OCR text
mode; GET /analizza/{token} turns the job result into the same analysis as a
native-text PDF.
"""
import pytest

from app.core.platform.models import DocumentJob, JobStatus, Scadenza, StatoScadenza
from app.core.platform_services.document_parsing_service import DocumentParsingService

from .test_caricamento_documenti_api import BASE, client, unita  # noqa: F401  (fixtures)

pytestmark = pytest.mark.integration

RISULTATO = {"testo": "...", "pagine": 1, "tipi": [
    {"codice": "RLI12", "riconosciuto": False, "campi": {}},
    {"codice": "PLANIMETRIA_CATASTALE", "riconosciuto": True, "campi": {
        "comune": {"valore": "Torino", "pagina": 1}, "foglio": {"valore": "12", "pagina": 1},
        "particella": {"valore": "345", "pagina": 1}, "subalterno": {"valore": "6", "pagina": 1}}},
]}


@pytest.fixture
def inviati(monkeypatch):
    jobs = []

    def submit(self, job):
        job.status = JobStatus.QUEUED
        jobs.append(job)
        self.db.commit()
    monkeypatch.setattr(DocumentParsingService, "_submit_to_parser", submit)
    return jobs


def _scansione(client):
    res = client.post(f"{BASE}/analizza", files={"file": ("plan.jpg", b"\xff\xd8\xffimmagine", "image/jpeg")})
    assert res.status_code == 200, res.text
    return res.json()


def _completa(db_session, job, risultato=RISULTATO):
    DocumentParsingService(db_session, job.tenant_schema).handle_callback(
        job.job_uuid, {"status": "finished", "result": risultato, "error": None})


def test_scansione_crea_lavoro_ocr(client, inviati):
    a = _scansione(client)
    assert a["esito"] == "in_lettura" and a["job_uuid"] == inviati[0].job_uuid
    assert inviati[0].parsing_service == "ocr_testo"
    assert inviati[0].parsing_config["modalita"] == "testo"
    assert {t["codice"] for t in inviati[0].parsing_config["tipi"]} >= {"APE", "PLANIMETRIA_CATASTALE"}
    assert client.get(f"{BASE}/analizza/{a['upload_token']}").json()["esito"] == "in_lettura"


def test_risultato_ocr_produce_analisi(client, inviati, unita, db_session):
    a = _scansione(client)
    _completa(db_session, inviati[0])
    b = client.get(f"{BASE}/analizza/{a['upload_token']}").json()
    assert b["esito"] == "pronto" and b["tipo_codice"] == "PLANIMETRIA_CATASTALE" and b["unita_id"] == unita.id


def test_conferma_chiude_attivita_ocr(client, inviati, unita, db_session):
    a = _scansione(client)
    _completa(db_session, inviati[0])
    b = client.get(f"{BASE}/analizza/{a['upload_token']}").json()
    res = client.post(f"{BASE}/conferma", json={"upload_token": a["upload_token"], "tipo_codice": b["tipo_codice"],
                                                "unita_id": b["unita_id"], "dati": {}, "differenze": []})
    assert res.status_code == 200, res.text
    job = db_session.query(DocumentJob).filter_by(job_uuid=a["job_uuid"]).one()
    assert db_session.get(Scadenza, job.scadenza_id).stato == StatoScadenza.COMPLETATA


def test_ocr_fallito_permette_scelta_manuale(client, inviati, unita, db_session):
    a = _scansione(client)
    DocumentParsingService(db_session, inviati[0].tenant_schema).handle_callback(
        inviati[0].job_uuid, {"status": "failed", "result": None, "error": "boom"})
    inviati[0].retry_count = inviati[0].max_retries
    inviati[0].status = JobStatus.FAILED
    db_session.flush()
    b = client.get(f"{BASE}/analizza/{a['upload_token']}").json()
    assert b["esito"] == "errore" and b["messaggio"] == "Lettura non riuscita: scegli tipo e immobile"
    c = client.post(f"{BASE}/rianalizza", json={"upload_token": a["upload_token"], "tipo_codice": "AGIBILITA",
                                                "unita_id": unita.id}).json()
    assert c["esito"] == "pronto"


def test_lavoro_ocr_senza_risposta_scade(client, inviati, db_session):
    """A job whose callback never arrives must not stay "in lettura" forever."""
    from datetime import datetime, timedelta
    a = _scansione(client)
    inviati[0].created_at = datetime.utcnow() - timedelta(minutes=31)
    db_session.flush()
    b = client.get(f"{BASE}/analizza/{a['upload_token']}").json()
    assert b["esito"] == "errore" and b["messaggio"] == "Lettura non riuscita: scegli tipo e immobile"
