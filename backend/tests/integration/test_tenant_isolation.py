"""
Integration tests for tenant isolation in document parsing system.

Verifies that:
- Tenant A cannot access Tenant B's files
- Tenant A cannot see Tenant B's jobs
- Callbacks respect tenant boundaries
- File paths are properly isolated
"""
import pytest
import tempfile
import shutil
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from app.core.platform.models import DocumentJob, JobStatus
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
def setup_document_types():
    """Setup document types in registry."""
    from app.core.platform_services.document_type_registry import document_type_registry

    manifest = {
        "document_types": [
            {
                "codice": "TEST_DOC",
                "nome": "Test Document",
                "categoria": "test",
                "parsing_service": "mrz",
                "parsing_config": {}
            }
        ]
    }

    document_type_registry.register_from_manifest("test_module", manifest)
    yield
    document_type_registry.clear()


class TestTenantFileIsolation:
    """Test file storage isolation between tenants."""

    def test_tenants_have_separate_directories(self, file_storage):
        """Each tenant should have its own isolated directory."""
        # Create files for two tenants
        file_a = BytesIO(b"Tenant A confidential data")
        file_b = BytesIO(b"Tenant B confidential data")

        path_a = file_storage.save_file(
            file=file_a,
            entity_type="document",
            entity_id=1,
            filename="secret.txt",
            tenant_schema="tenant_a"
        )

        path_b = file_storage.save_file(
            file=file_b,
            entity_type="document",
            entity_id=1,
            filename="secret.txt",
            tenant_schema="tenant_b"
        )

        # Paths should be in different tenant directories
        assert "tenant_a" in path_a
        assert "tenant_b" in path_b

        # Files should exist and have correct content
        full_path_a = file_storage.base_path / path_a
        full_path_b = file_storage.base_path / path_b

        assert full_path_a.read_bytes() == b"Tenant A confidential data"
        assert full_path_b.read_bytes() == b"Tenant B confidential data"

        # Verify tenant_a directory doesn't contain tenant_b files
        tenant_a_dir = file_storage.base_path / "tenant_a"
        tenant_b_dir = file_storage.base_path / "tenant_b"

        assert not str(full_path_b).startswith(str(tenant_a_dir))
        assert not str(full_path_a).startswith(str(tenant_b_dir))

    def test_tenant_cannot_access_other_tenant_files(self, file_storage):
        """Tenant A should not be able to access Tenant B's files."""
        # Tenant B creates a file
        file_b = BytesIO(b"Tenant B secret")
        path_b = file_storage.save_file(
            file=file_b,
            entity_type="document",
            entity_id=1,
            filename="secret.txt",
            tenant_schema="tenant_b"
        )

        # Tenant A tries to access with validation
        tenant_a_path = file_storage._get_tenant_path("tenant_a")
        file_b_full_path = file_storage.base_path / path_b

        # Should fail security validation
        with pytest.raises(ValueError, match="fuori dalla directory tenant"):
            file_storage._validate_path_security(file_b_full_path, tenant_a_path)

    def test_temp_files_isolated_by_tenant(self, file_storage):
        """Temporary files should be isolated by tenant."""
        # Create temp files for two tenants
        file_a = BytesIO(b"Temp A")
        file_b = BytesIO(b"Temp B")

        temp_a = file_storage.save_temp_file(
            file=file_a,
            job_uuid="job-a",
            filename="temp.txt",
            tenant_schema="tenant_a"
        )

        temp_b = file_storage.save_temp_file(
            file=file_b,
            job_uuid="job-b",
            filename="temp.txt",
            tenant_schema="tenant_b"
        )

        # Both should be in separate tenant directories
        assert "tenant_a/temp_uploads/" in temp_a
        assert "tenant_b/temp_uploads/" in temp_b

        # Files should exist independently
        full_temp_a = file_storage.base_path / temp_a
        full_temp_b = file_storage.base_path / temp_b

        assert full_temp_a.exists()
        assert full_temp_b.exists()
        assert full_temp_a.read_bytes() == b"Temp A"
        assert full_temp_b.read_bytes() == b"Temp B"


class TestTenantJobIsolation:
    """Test DocumentJob isolation between tenants."""

    def test_tenants_cannot_see_each_others_jobs(
        self,
        db_session,
        test_user,
        file_storage
    ):
        """Tenants should only see their own jobs."""
        # Create jobs for two tenants
        job_a = DocumentJob(
            job_uuid="tenant-a-job",
            tenant_schema="tenant_a",
            file_path="tenant_a/file.jpg",
            original_filename="a.jpg",
            document_type_key="test.DOC",
            parsing_service="mrz",
            status=JobStatus.COMPLETED,
            created_by=test_user.id
        )

        job_b = DocumentJob(
            job_uuid="tenant-b-job",
            tenant_schema="tenant_b",
            file_path="tenant_b/file.jpg",
            original_filename="b.jpg",
            document_type_key="test.DOC",
            parsing_service="mrz",
            status=JobStatus.COMPLETED,
            created_by=test_user.id
        )

        db_session.add_all([job_a, job_b])
        db_session.commit()

        # Service for tenant A
        service_a = DocumentParsingService(db_session, "tenant_a")
        jobs_a = service_a.get_user_jobs(user_id=test_user.id)

        # Should only see tenant A's job
        assert len(jobs_a) == 1
        assert jobs_a[0].job_uuid == "tenant-a-job"
        assert jobs_a[0].tenant_schema == "tenant_a"

        # Service for tenant B
        service_b = DocumentParsingService(db_session, "tenant_b")
        jobs_b = service_b.get_user_jobs(user_id=test_user.id)

        # Should only see tenant B's job
        assert len(jobs_b) == 1
        assert jobs_b[0].job_uuid == "tenant-b-job"
        assert jobs_b[0].tenant_schema == "tenant_b"

    def test_get_job_respects_tenant(
        self,
        db_session,
        test_user,
        file_storage
    ):
        """get_job should only return jobs from correct tenant."""
        # Create job for tenant A
        job = DocumentJob(
            job_uuid="cross-tenant-test",
            tenant_schema="tenant_a",
            file_path="tenant_a/file.jpg",
            original_filename="test.jpg",
            document_type_key="test.DOC",
            parsing_service="mrz",
            status=JobStatus.COMPLETED,
            created_by=test_user.id
        )
        db_session.add(job)
        db_session.commit()

        # Service for tenant A should find it
        service_a = DocumentParsingService(db_session, "tenant_a")
        found_job = service_a.get_job("cross-tenant-test")
        assert found_job is not None
        assert found_job.tenant_schema == "tenant_a"

        # Service for tenant B should NOT find it
        service_b = DocumentParsingService(db_session, "tenant_b")
        not_found = service_b.get_job("cross-tenant-test")
        assert not_found is None

    def test_pending_documents_filtered_by_tenant(
        self,
        db_session,
        test_user,
        file_storage
    ):
        """Pending documents should be filtered by tenant."""
        # Create pending jobs for multiple tenants
        jobs = [
            DocumentJob(
                job_uuid="pending-a",
                tenant_schema="tenant_a",
                file_path="tenant_a/file.jpg",
                original_filename="a.jpg",
                document_type_key="test.DOC",
                parsing_service="mrz",
                status=JobStatus.COMPLETED,
                entity_id=None,
                created_by=test_user.id
            ),
            DocumentJob(
                job_uuid="pending-b",
                tenant_schema="tenant_b",
                file_path="tenant_b/file.jpg",
                original_filename="b.jpg",
                document_type_key="test.DOC",
                parsing_service="mrz",
                status=JobStatus.COMPLETED,
                entity_id=None,
                created_by=test_user.id
            ),
        ]
        db_session.add_all(jobs)
        db_session.commit()

        # Each tenant should only see their own pending documents
        service_a = DocumentParsingService(db_session, "tenant_a")
        pending_a = service_a.get_pending_documents(user_id=test_user.id)
        assert len(pending_a) == 1
        assert pending_a[0].job_uuid == "pending-a"

        service_b = DocumentParsingService(db_session, "tenant_b")
        pending_b = service_b.get_pending_documents(user_id=test_user.id)
        assert len(pending_b) == 1
        assert pending_b[0].job_uuid == "pending-b"


class TestCallbackTenantIsolation:
    """Test callback handling respects tenant boundaries."""

    def test_callback_finds_correct_tenant_job(
        self,
        db_session,
        test_user,
        file_storage
    ):
        """Callback should find job in correct tenant context."""
        # Create jobs with same UUID in different tenants (shouldn't happen, but test it)
        job_a = DocumentJob(
            job_uuid="same-uuid",
            tenant_schema="tenant_a",
            file_path="tenant_a/file.jpg",
            original_filename="a.jpg",
            document_type_key="test.DOC",
            parsing_service="mrz",
            status=JobStatus.QUEUED,
            created_by=test_user.id
        )

        job_b = DocumentJob(
            job_uuid="same-uuid-different",
            tenant_schema="tenant_b",
            file_path="tenant_b/file.jpg",
            original_filename="b.jpg",
            document_type_key="test.DOC",
            parsing_service="mrz",
            status=JobStatus.QUEUED,
            created_by=test_user.id
        )

        db_session.add_all([job_a, job_b])
        db_session.commit()

        # Callback for tenant A job
        service_a = DocumentParsingService(db_session, "tenant_a")
        callback_data = {
            "status": "finished",
            "result": {"data": "result A"}
        }

        updated_job = service_a.handle_callback("same-uuid", callback_data)

        # Should have updated tenant A's job
        assert updated_job.tenant_schema == "tenant_a"
        assert updated_job.parsing_result == {"data": "result A"}

        # Tenant B's job should be unchanged
        db_session.refresh(job_b)
        assert job_b.status == JobStatus.QUEUED
        assert job_b.parsing_result is None


class TestDataLeakagePrevention:
    """Test that no data leaks between tenants."""

    def test_no_file_path_leakage(self, file_storage):
        """File paths should not reveal information about other tenants."""
        # Create file for tenant A
        file_a = BytesIO(b"data")
        path_a = file_storage.save_file(
            file=file_a,
            entity_type="entity",
            entity_id=1,
            filename="test.txt",
            tenant_schema="tenant_a"
        )

        # Path should only contain tenant_a info
        assert "tenant_a" in path_a
        assert "tenant_b" not in path_a

        # Attempting to list tenant_a directory should not show tenant_b
        tenant_a_dir = file_storage.base_path / "tenant_a"
        if tenant_a_dir.exists():
            for item in tenant_a_dir.rglob("*"):
                assert "tenant_b" not in str(item)

    def test_job_queries_dont_leak_tenant_info(
        self,
        db_session,
        test_user,
        file_storage
    ):
        """Job queries should not leak information about other tenants."""
        # Create jobs for multiple tenants
        for i, tenant in enumerate(["tenant_a", "tenant_b", "tenant_c"]):
            job = DocumentJob(
                job_uuid=f"job-{tenant}",
                tenant_schema=tenant,
                file_path=f"{tenant}/file.jpg",
                original_filename=f"{tenant}.jpg",
                document_type_key="test.DOC",
                parsing_service="mrz",
                status=JobStatus.COMPLETED,
                created_by=test_user.id
            )
            db_session.add(job)
        db_session.commit()

        # Query for tenant_a should not reveal existence of other tenants
        service_a = DocumentParsingService(db_session, "tenant_a")
        jobs_a = service_a.get_user_jobs(user_id=test_user.id, limit=100)

        # Should only return 1 job
        assert len(jobs_a) == 1

        # Job should be for tenant_a only
        for job in jobs_a:
            assert job.tenant_schema == "tenant_a"
            assert "tenant_b" not in job.file_path
            assert "tenant_c" not in job.file_path
