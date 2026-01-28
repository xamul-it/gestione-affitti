"""
End-to-end integration tests for document parsing workflow.

Tests complete workflow:
1. User uploads identity document
2. Document parsed by MRZ service (mocked)
3. Callback updates job status
4. Notification (Scadenza) created
5. User completes anagrafica creation
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from io import BytesIO
from datetime import date, datetime
from unittest.mock import patch, MagicMock

from app.core.platform.models import DocumentJob, JobStatus, Scadenza, StatoScadenza
from app.core.platform_services import DocumentParsingService
from app.core.file_storage import FileStorage


@pytest.fixture
def temp_storage():
    """Create temporary storage for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def file_storage(temp_storage):
    """Create FileStorage with temp directory."""
    return FileStorage(base_path=temp_storage)


@pytest.fixture
def mock_mrz_service():
    """Mock MRZ service HTTP responses."""
    with patch('app.core.platform_services.document_parsing_service.httpx.Client') as mock_client:
        # Mock successful submission
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"job_id": "mock-job-id", "status": "queued"}

        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_client
        mock_context.__exit__.return_value = None

        mock_client.return_value = mock_context
        mock_client.post.return_value = mock_response

        yield mock_client


@pytest.fixture
def sample_mrz_result():
    """Sample MRZ parsing result."""
    return {
        "mrz_valid": True,
        "document_number": "CA12345AB",
        "surname": "ROSSI",
        "given_names": "MARIO",
        "birth_date": "1980-01-15",
        "birth_place": "ROMA",
        "codice_fiscale": "RSSMRA80A15H501U",
        "expiry_date": "2030-12-31",
        "confidence_score": 0.95,
        "needs_review": False
    }


@pytest.fixture
def setup_document_types(db_session):
    """Setup document types in registry."""
    from app.core.platform_services.document_type_registry import document_type_registry

    manifest = {
        "document_types": [
            {
                "codice": "CARTA_IDENTITA",
                "nome": "Carta d'Identità",
                "categoria": "identita",
                "richiede_scadenza": True,
                "parsing_service": "mrz",
                "parsing_config": {"mrz_format": "td1"}
            }
        ]
    }

    document_type_registry.register_from_manifest("anagrafica_italiana", manifest)
    yield
    document_type_registry.clear()


class TestDocumentUploadAndParsing:
    """Test document upload and parsing initiation."""

    def test_upload_and_parse_creates_job(
        self,
        db_session,
        test_user,
        file_storage,
        mock_mrz_service,
        setup_document_types
    ):
        """Uploading document should create DocumentJob and submit to service."""
        # Patch file_storage globally
        with patch('app.core.platform_services.document_parsing_service.file_storage', file_storage):
            service = DocumentParsingService(db_session, "tenant_test")

            # Create fake file
            fake_file = BytesIO(b"fake image data")
            fake_file.filename = "carta_identita.jpg"
            fake_file.content_type = "image/jpeg"

            # Upload and parse
            job = service.upload_and_parse(
                file=fake_file,
                document_type_key="anagrafica_italiana.CARTA_IDENTITA",
                entity_type=None,
                entity_id=None,
                user_id=test_user.id
            )

            # Verify job created
            assert job is not None
            assert job.status == JobStatus.QUEUED
            assert job.tenant_schema == "tenant_test"
            assert job.original_filename == "carta_identita.jpg"
            assert job.document_type_key == "anagrafica_italiana.CARTA_IDENTITA"
            assert job.parsing_service == "mrz"
            assert job.created_by == test_user.id

            # Verify file saved to temp storage
            assert job.file_path.startswith("tenant_test/temp_uploads/")

    def test_upload_invalid_document_type(self, db_session, test_user):
        """Uploading with invalid document type should fail."""
        service = DocumentParsingService(db_session, "tenant_test")

        fake_file = BytesIO(b"data")
        fake_file.filename = "test.jpg"

        with pytest.raises(Exception, match="non valido"):
            service.upload_and_parse(
                file=fake_file,
                document_type_key="invalid.INVALID",
                user_id=test_user.id
            )


class TestCallbackHandling:
    """Test callback handling from parsing service."""

    def test_callback_success_updates_job(
        self,
        db_session,
        test_user,
        file_storage,
        sample_mrz_result,
        setup_document_types
    ):
        """Successful callback should update job and create notification."""
        with patch('app.core.platform_services.document_parsing_service.file_storage', file_storage):
            service = DocumentParsingService(db_session, "tenant_test")

            # Create job manually
            job = DocumentJob(
                job_uuid="test-callback-job",
                tenant_schema="tenant_test",
                file_path="tenant_test/temp_uploads/test/file.jpg",
                original_filename="carta.jpg",
                mime_type="image/jpeg",
                document_type_key="anagrafica_italiana.CARTA_IDENTITA",
                parsing_service="mrz",
                parsing_config={},
                status=JobStatus.QUEUED,
                created_by=test_user.id
            )
            db_session.add(job)
            db_session.commit()

            # Simulate callback
            callback_data = {
                "job_id": "test-callback-job",
                "status": "finished",
                "result": sample_mrz_result
            }

            updated_job = service.handle_callback("test-callback-job", callback_data)

            # Verify job updated
            assert updated_job.status == JobStatus.COMPLETED
            assert updated_job.parsing_result == sample_mrz_result
            assert updated_job.confidence_score == 95  # 0.95 * 100
            assert updated_job.needs_review == False
            assert updated_job.completed_at is not None

            # Verify notification created
            assert updated_job.scadenza_id is not None

            scadenza = db_session.query(Scadenza).filter(
                Scadenza.id == updated_job.scadenza_id
            ).first()

            assert scadenza is not None
            assert scadenza.stato == StatoScadenza.ATTIVA
            assert "Completa anagrafica" in scadenza.titolo
            assert scadenza.creato_da == test_user.id

    def test_callback_failure_with_retry(
        self,
        db_session,
        test_user,
        file_storage,
        setup_document_types
    ):
        """Failed callback should mark job as failed and retry if possible."""
        with patch('app.core.platform_services.document_parsing_service.file_storage', file_storage):
            service = DocumentParsingService(db_session, "tenant_test")

            # Create job with retries available
            job = DocumentJob(
                job_uuid="test-retry-job",
                tenant_schema="tenant_test",
                file_path="tenant_test/temp_uploads/test/file.jpg",
                original_filename="carta.jpg",
                document_type_key="anagrafica_italiana.CARTA_IDENTITA",
                parsing_service="mrz",
                status=JobStatus.QUEUED,
                retry_count=0,
                max_retries=3,
                created_by=test_user.id
            )
            db_session.add(job)
            db_session.commit()

            # Mock the retry submission to succeed
            with patch.object(service, '_submit_to_parser') as mock_submit:
                # Simulate failed callback
                callback_data = {
                    "job_id": "test-retry-job",
                    "status": "failed",
                    "error": "MRZ parsing failed"
                }

                updated_job = service.handle_callback("test-retry-job", callback_data)

                # Should have incremented retry and set to PENDING
                assert updated_job.retry_count == 1
                assert updated_job.status == JobStatus.PENDING
                assert mock_submit.called


class TestNotificationCreation:
    """Test notification (Scadenza) creation."""

    def test_notification_priority_based_on_confidence(
        self,
        db_session,
        test_user,
        file_storage,
        setup_document_types
    ):
        """Notification priority should be based on confidence score."""
        from app.core.platform.models import PrioritaScadenza

        with patch('app.core.platform_services.document_parsing_service.file_storage', file_storage):
            service = DocumentParsingService(db_session, "tenant_test")

            test_cases = [
                (95, PrioritaScadenza.BASSA),   # High confidence
                (75, PrioritaScadenza.MEDIA),   # Medium confidence
                (50, PrioritaScadenza.ALTA),    # Low confidence
            ]

            for confidence, expected_priority in test_cases:
                job = DocumentJob(
                    job_uuid=f"test-priority-{confidence}",
                    tenant_schema="tenant_test",
                    file_path="test/file.jpg",
                    original_filename="test.jpg",
                    document_type_key="anagrafica_italiana.CARTA_IDENTITA",
                    parsing_service="mrz",
                    status=JobStatus.QUEUED,
                    created_by=test_user.id
                )
                db_session.add(job)
                db_session.commit()

                # Simulate callback with specific confidence
                callback_data = {
                    "status": "finished",
                    "result": {
                        "confidence_score": confidence / 100,
                        "needs_review": confidence < 80
                    }
                }

                service.handle_callback(job.job_uuid, callback_data)
                db_session.refresh(job)

                # Check notification priority
                scadenza = db_session.query(Scadenza).filter(
                    Scadenza.id == job.scadenza_id
                ).first()

                assert scadenza.priorita == expected_priority


class TestCompleteAnagraficaWorkflow:
    """Test complete anagrafica creation from document."""

    def test_complete_workflow_end_to_end(
        self,
        db_session,
        test_user,
        file_storage,
        sample_mrz_result,
        setup_document_types
    ):
        """Test complete workflow from upload to anagrafica creation."""
        from app.core.platform_services.document_parsing_service import DocumentParsingService

        # Patch file storage
        with patch('app.core.platform_services.document_parsing_service.file_storage', file_storage):
            with patch('app.core.file_storage.file_storage', file_storage):
                service = DocumentParsingService(db_session, "tenant_test")

                # Step 1: Upload document (mocked)
                fake_file = BytesIO(b"image data")
                fake_file.filename = "carta.jpg"
                fake_file.content_type = "image/jpeg"

                with patch('app.core.platform_services.document_parsing_service.httpx.Client'):
                    job = service.upload_and_parse(
                        file=fake_file,
                        document_type_key="anagrafica_italiana.CARTA_IDENTITA",
                        user_id=test_user.id
                    )

                # Verify job created
                assert job.status == JobStatus.QUEUED

                # Step 2: Simulate callback
                callback_data = {
                    "job_id": job.job_uuid,
                    "status": "finished",
                    "result": sample_mrz_result
                }

                updated_job = service.handle_callback(job.job_uuid, callback_data)

                # Verify job completed and notification created
                assert updated_job.status == JobStatus.COMPLETED
                assert updated_job.scadenza_id is not None

                # Step 3: Simulate user completing anagrafica
                # (This would typically be done via API endpoint)
                from modules.anagrafica_italiana.models import SoggettoAnagrafico, TipoSoggetto

                soggetto = SoggettoAnagrafico(
                    tipo_soggetto=TipoSoggetto.PERSONA_FISICA,
                    nome=sample_mrz_result["given_names"],
                    cognome=sample_mrz_result["surname"],
                    codice_fiscale=sample_mrz_result["codice_fiscale"],
                    attivo=True
                )
                db_session.add(soggetto)
                db_session.commit()

                # Link job to soggetto
                updated_job.entity_type = "SOGGETTO_ANAGRAFICO"
                updated_job.entity_id = soggetto.id
                db_session.commit()

                # Complete notification
                scadenza = db_session.query(Scadenza).get(updated_job.scadenza_id)
                scadenza.stato = StatoScadenza.COMPLETATA
                scadenza.completato_da = test_user.id
                scadenza.completato_il = datetime.utcnow()
                db_session.commit()

                # Verify final state
                assert soggetto.id is not None
                assert updated_job.entity_id == soggetto.id
                assert scadenza.stato == StatoScadenza.COMPLETATA


class TestTenantIsolation:
    """Test tenant isolation in document parsing."""

    def test_jobs_isolated_by_tenant(
        self,
        db_session,
        test_user,
        file_storage,
        setup_document_types
    ):
        """Jobs should be isolated by tenant."""
        with patch('app.core.platform_services.document_parsing_service.file_storage', file_storage):
            service_a = DocumentParsingService(db_session, "tenant_a")
            service_b = DocumentParsingService(db_session, "tenant_b")

            # Create jobs for different tenants
            job_a = DocumentJob(
                job_uuid="tenant-a-job",
                tenant_schema="tenant_a",
                file_path="tenant_a/file.jpg",
                original_filename="a.jpg",
                document_type_key="anagrafica_italiana.CARTA_IDENTITA",
                parsing_service="mrz",
                status=JobStatus.PENDING,
                created_by=test_user.id
            )

            job_b = DocumentJob(
                job_uuid="tenant-b-job",
                tenant_schema="tenant_b",
                file_path="tenant_b/file.jpg",
                original_filename="b.jpg",
                document_type_key="anagrafica_italiana.CARTA_IDENTITA",
                parsing_service="mrz",
                status=JobStatus.PENDING,
                created_by=test_user.id
            )

            db_session.add_all([job_a, job_b])
            db_session.commit()

            # Service A should only see tenant A jobs
            jobs_a = service_a.get_user_jobs(user_id=test_user.id)
            assert len(jobs_a) == 1
            assert jobs_a[0].tenant_schema == "tenant_a"

            # Service B should only see tenant B jobs
            jobs_b = service_b.get_user_jobs(user_id=test_user.id)
            assert len(jobs_b) == 1
            assert jobs_b[0].tenant_schema == "tenant_b"

    def test_file_paths_include_tenant(
        self,
        db_session,
        test_user,
        file_storage,
        setup_document_types
    ):
        """File paths should include tenant for isolation."""
        with patch('app.core.platform_services.document_parsing_service.file_storage', file_storage):
            with patch('app.core.platform_services.document_parsing_service.httpx.Client'):
                service = DocumentParsingService(db_session, "tenant_test")

                fake_file = BytesIO(b"data")
                fake_file.filename = "test.jpg"
                fake_file.content_type = "image/jpeg"

                job = service.upload_and_parse(
                    file=fake_file,
                    document_type_key="anagrafica_italiana.CARTA_IDENTITA",
                    user_id=test_user.id
                )

                # File path should include tenant
                assert job.file_path.startswith("tenant_test/")


class TestErrorHandling:
    """Test error handling in document parsing."""

    def test_callback_for_nonexistent_job(self, db_session, file_storage):
        """Callback for nonexistent job should raise error."""
        service = DocumentParsingService(db_session, "tenant_test")

        callback_data = {
            "job_id": "nonexistent",
            "status": "finished",
            "result": {}
        }

        with pytest.raises(Exception, match="non trovato"):
            service.handle_callback("nonexistent", callback_data)

    def test_get_pending_documents_filters_correctly(
        self,
        db_session,
        test_user,
        file_storage
    ):
        """get_pending_documents should only return completed jobs without entity_id."""
        service = DocumentParsingService(db_session, "tenant_test")

        # Create various jobs
        jobs = [
            # Pending document (should be returned)
            DocumentJob(
                job_uuid="pending-1",
                tenant_schema="tenant_test",
                file_path="test1.jpg",
                original_filename="test1.jpg",
                document_type_key="test.DOC",
                parsing_service="mrz",
                status=JobStatus.COMPLETED,
                entity_id=None,  # Not linked yet
                created_by=test_user.id
            ),
            # Completed and linked (should NOT be returned)
            DocumentJob(
                job_uuid="linked-1",
                tenant_schema="tenant_test",
                file_path="test2.jpg",
                original_filename="test2.jpg",
                document_type_key="test.DOC",
                parsing_service="mrz",
                status=JobStatus.COMPLETED,
                entity_id=123,  # Already linked
                created_by=test_user.id
            ),
            # Not completed yet (should NOT be returned)
            DocumentJob(
                job_uuid="pending-parse",
                tenant_schema="tenant_test",
                file_path="test3.jpg",
                original_filename="test3.jpg",
                document_type_key="test.DOC",
                parsing_service="mrz",
                status=JobStatus.QUEUED,  # Still processing
                entity_id=None,
                created_by=test_user.id
            ),
        ]

        db_session.add_all(jobs)
        db_session.commit()

        # Get pending documents
        pending = service.get_pending_documents(user_id=test_user.id)

        # Should only return the first job
        assert len(pending) == 1
        assert pending[0].job_uuid == "pending-1"
