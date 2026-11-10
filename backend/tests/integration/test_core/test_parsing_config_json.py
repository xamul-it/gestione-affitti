"""
DocumentParsingService sends the parsing_config as form fields: nested values
(the OCR text mode's `tipi`) travel as JSON strings; a job can carry its own
title for the review activity.
"""
import io
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.core.platform.models import Scadenza
from app.core.platform.models.parsing_service_config import ParsingServiceConfig
from app.core.platform_services.document_parsing_service import DocumentParsingService
from tests.integration.conftest import TEST_TENANT

pytestmark = pytest.mark.integration


@pytest.fixture
def servizio(db_session, tmp_path, monkeypatch):
    from app.core.file_storage import file_storage
    monkeypatch.setattr(file_storage, "base_path", tmp_path)
    cfg = db_session.query(ParsingServiceConfig).filter_by(service_key="ocr_testo").first() \
        or ParsingServiceConfig(service_key="ocr_testo")
    cfg.transport_type, cfg.endpoint_url, cfg.enabled = "HTTP", "http://ocr.test/testo", "true"
    db_session.add(cfg)
    db_session.flush()
    with patch("app.core.platform_services.document_parsing_service.httpx.Client") as client:
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"job_id": "x", "status": "queued"}
        ctx = MagicMock()
        ctx.__enter__.return_value = client
        client.return_value = ctx
        client.post.return_value = resp
        yield client


def _job(db_session, test_user_id, config):
    f = SimpleNamespace(file=io.BytesIO(b"img"), filename="scan.jpg", content_type="image/jpeg")
    return DocumentParsingService(db_session, TEST_TENANT).upload_and_parse(
        f, "immobili.ALTRO_IMMOBILE", user_id=test_user_id,
        parsing_service_override="ocr_testo", parsing_config_override=config)


@pytest.fixture
def user_id(db_session, unique_suffix):
    from app.core.auth.models import User
    u = User(username=f"pj{unique_suffix}", email=f"pj{unique_suffix}@x.it", hashed_password="x")
    db_session.add(u)
    db_session.flush()
    return u.id


def test_config_annidata_inviata_come_json(db_session, servizio, user_id):
    tipi = [{"codice": "APE", "riconosci": ["x"], "campi": {"foglio": "(?P<v>\\d+)"}}]
    _job(db_session, user_id, {"modalita": "testo", "tipi": tipi})
    data = servizio.post.call_args.kwargs["data"]
    assert data["modalita"] == "testo"
    assert json.loads(data["tipi"]) == tipi


def test_titolo_attivita_personalizzato(db_session, servizio, user_id):
    job = _job(db_session, user_id, {"modalita": "testo", "titolo_attivita": "Documento immobile letto: scan.jpg"})
    DocumentParsingService(db_session, TEST_TENANT).handle_callback(
        job.job_uuid, {"status": "finished", "result": {"testo": "", "tipi": []}, "error": None})
    db_session.refresh(job)
    assert db_session.get(Scadenza, job.scadenza_id).titolo == "Documento immobile letto: scan.jpg"
