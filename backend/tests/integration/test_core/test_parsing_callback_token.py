"""
The parsing callback has no user authentication (an external service calls
it), so it requires a per-job token: an HMAC of the job uuid with SECRET_KEY,
put in the callback URL the backend hands to the service. Without it, anyone
knowing a job uuid could write fake parsed data on the job's document.
"""
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.platform.models import DocumentJob, JobStatus
from app.core.platform_services.document_parsing_service import DocumentParsingService, callback_token
from app.main import app
from tests.integration.conftest import TEST_TENANT

pytestmark = pytest.mark.integration


@pytest.fixture
def job(db_session, unique_suffix):
    from app.core.auth.models import User
    user = User(username=f"cb{unique_suffix}", email=f"cb{unique_suffix}@x.it", hashed_password="x")
    db_session.add(user)
    db_session.flush()
    j = DocumentJob(created_by=user.id,
        job_uuid=f"cb-{unique_suffix}", tenant_schema=TEST_TENANT,
        file_path="x.jpg", original_filename="x.jpg", parsing_service="mrz",
        document_type_key="anagrafica_italiana.CARTA_IDENTITA", status=JobStatus.PROCESSING,
    )
    db_session.add(j)
    db_session.flush()
    return j


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)


PAYLOAD = {"status": "failed", "result": None, "error": "boom"}


def test_url_di_richiamata_porta_il_token(db_session, job):
    url = DocumentParsingService(db_session, TEST_TENANT)._resolve_callback_url(job)
    assert parse_qs(urlparse(url).query)["token"] == [callback_token(job.job_uuid)]


def test_richiamata_senza_token_rifiutata(client, job):
    res = client.post(f"/api/v1/document-parsing/callback/{job.job_uuid}", json=PAYLOAD)
    assert res.status_code == 403


def test_richiamata_con_token_sbagliato_rifiutata(client, job):
    res = client.post(f"/api/v1/document-parsing/callback/{job.job_uuid}?token=abc", json=PAYLOAD)
    assert res.status_code == 403


def test_token_di_un_altro_job_rifiutato(client, job):
    res = client.post(f"/api/v1/document-parsing/callback/{job.job_uuid}?token={callback_token('altro')}",
                      json=PAYLOAD)
    assert res.status_code == 403


def test_richiamata_con_token_accettata(client, job):
    res = client.post(f"/api/v1/document-parsing/callback/{job.job_uuid}?token={callback_token(job.job_uuid)}",
                      json=PAYLOAD)
    assert res.status_code == 200


def test_richiamata_su_job_concluso_rifiutata(client, job, db_session):
    """A leaked token can't be replayed once the job has its result."""
    job.status = JobStatus.COMPLETED
    db_session.flush()
    res = client.post(f"/api/v1/document-parsing/callback/{job.job_uuid}?token={callback_token(job.job_uuid)}",
                      json=PAYLOAD)
    assert res.status_code == 409


def test_token_oscurato_nel_log(db_session, job):
    from app.core.platform.models import DocumentParsingLog
    service = DocumentParsingService(db_session, TEST_TENANT)
    url = service._resolve_callback_url(job)
    service._log_parsing_event(job=job, direction="REQUEST", url="http://svc/mrz",
                               request_payload={"callback_url": url})
    db_session.flush()
    log = db_session.query(DocumentParsingLog).filter_by(job_uuid=job.job_uuid).one()
    assert callback_token(job.job_uuid) not in str(log.request_payload)
