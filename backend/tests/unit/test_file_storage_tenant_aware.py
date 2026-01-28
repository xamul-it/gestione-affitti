"""
Unit tests for tenant-aware file storage.

Tests:
- Tenant isolation (tenant A cannot access tenant B files)
- Directory traversal prevention
- save_temp_file() functionality
- move_from_temp() functionality
- Path resolution security
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from io import BytesIO

from app.core.file_storage import FileStorage


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def file_storage(temp_storage_dir):
    """Create FileStorage instance with temp directory."""
    return FileStorage(base_path=temp_storage_dir)


class TestTenantValidation:
    """Test tenant schema validation."""

    def test_validate_tenant_schema_valid(self, file_storage):
        """Valid tenant schemas should pass validation."""
        valid_schemas = [
            "tenant_test",
            "tenant_produzione",
            "tenant_123",
            "tenant_abc_def",
        ]

        for schema in valid_schemas:
            # Should not raise
            file_storage._validate_tenant_schema(schema)

    def test_validate_tenant_schema_invalid_characters(self, file_storage):
        """Invalid characters should raise ValueError."""
        invalid_schemas = [
            "tenant/../etc",  # Directory traversal
            "tenant/test",     # Slash
            "tenant\\test",    # Backslash
            "tenant test",     # Space
            "tenant@test",     # Special char
            "tenant-test",     # Hyphen (not allowed)
        ]

        for schema in invalid_schemas:
            with pytest.raises(ValueError, match="non valido"):
                file_storage._validate_tenant_schema(schema)

    def test_validate_tenant_schema_empty(self, file_storage):
        """Empty tenant schema should raise ValueError."""
        with pytest.raises(ValueError, match="obbligatorio"):
            file_storage._validate_tenant_schema("")

    def test_validate_tenant_schema_none(self, file_storage):
        """None tenant schema should raise ValueError."""
        with pytest.raises(ValueError, match="obbligatorio"):
            file_storage._validate_tenant_schema(None)


class TestTenantIsolation:
    """Test tenant data isolation."""

    def test_save_file_creates_tenant_directory(self, file_storage):
        """Saving file should create tenant-specific directory."""
        file_content = BytesIO(b"test content")

        relative_path = file_storage.save_file(
            file=file_content,
            entity_type="test_entity",
            entity_id=1,
            filename="test.txt",
            tenant_schema="tenant_test"
        )

        # Path should include tenant
        assert relative_path.startswith("tenant_test/")

        # File should exist
        full_path = file_storage.base_path / relative_path
        assert full_path.exists()
        assert full_path.read_bytes() == b"test content"

    def test_tenant_a_cannot_access_tenant_b_files(self, file_storage):
        """Tenant A should not be able to access Tenant B files."""
        # Create file for tenant_a
        file_a = BytesIO(b"tenant A data")
        path_a = file_storage.save_file(
            file=file_a,
            entity_type="entity",
            entity_id=1,
            filename="file_a.txt",
            tenant_schema="tenant_a"
        )

        # Create file for tenant_b
        file_b = BytesIO(b"tenant B data")
        path_b = file_storage.save_file(
            file=file_b,
            entity_type="entity",
            entity_id=1,
            filename="file_b.txt",
            tenant_schema="tenant_b"
        )

        # Verify files are in different directories
        assert "tenant_a" in path_a
        assert "tenant_b" in path_b

        # Verify tenant_a path does not resolve to tenant_b file
        tenant_a_dir = file_storage.base_path / "tenant_a"
        tenant_b_file = file_storage.base_path / path_b

        # tenant_b file should NOT be under tenant_a directory
        assert not str(tenant_b_file).startswith(str(tenant_a_dir))

    def test_different_tenants_same_entity_id(self, file_storage):
        """Different tenants can have same entity_id without conflict."""
        # Both tenants create file for entity_id=1
        file_1 = BytesIO(b"tenant 1 content")
        path_1 = file_storage.save_file(
            file=file_1,
            entity_type="entity",
            entity_id=1,
            filename="test.txt",
            tenant_schema="tenant_1"
        )

        file_2 = BytesIO(b"tenant 2 content")
        path_2 = file_storage.save_file(
            file=file_2,
            entity_type="entity",
            entity_id=1,
            filename="test.txt",
            tenant_schema="tenant_2"
        )

        # Both files should exist
        full_path_1 = file_storage.base_path / path_1
        full_path_2 = file_storage.base_path / path_2

        assert full_path_1.exists()
        assert full_path_2.exists()

        # Content should be different
        assert full_path_1.read_bytes() == b"tenant 1 content"
        assert full_path_2.read_bytes() == b"tenant 2 content"


class TestDirectoryTraversalPrevention:
    """Test directory traversal attack prevention."""

    def test_path_security_validation(self, file_storage):
        """Path validation should prevent directory traversal."""
        tenant_path = file_storage._get_tenant_path("tenant_test")

        # Valid path under tenant
        valid_path = tenant_path / "entity" / "1" / "file.txt"
        file_storage._validate_path_security(valid_path, tenant_path)  # Should not raise

        # Invalid path outside tenant
        invalid_path = file_storage.base_path / "other_tenant" / "file.txt"
        with pytest.raises(ValueError, match="fuori dalla directory tenant"):
            file_storage._validate_path_security(invalid_path, tenant_path)

    def test_cannot_access_parent_directory(self, file_storage):
        """Cannot use .. to access parent directory."""
        # Create a file normally
        file_content = BytesIO(b"test")
        path = file_storage.save_file(
            file=file_content,
            entity_type="entity",
            entity_id=1,
            filename="test.txt",
            tenant_schema="tenant_test"
        )

        # Try to construct path with ..
        tenant_path = file_storage._get_tenant_path("tenant_test")
        malicious_path = tenant_path / ".." / "other_tenant" / "secret.txt"

        # Should fail validation
        with pytest.raises(ValueError):
            file_storage._validate_path_security(malicious_path, tenant_path)


class TestTempFileOperations:
    """Test temporary file operations for async workflows."""

    def test_save_temp_file(self, file_storage):
        """save_temp_file should create file in temp_uploads directory."""
        file_content = BytesIO(b"temp file content")
        job_uuid = "test-job-uuid-123"

        relative_path = file_storage.save_temp_file(
            file=file_content,
            job_uuid=job_uuid,
            filename="document.jpg",
            tenant_schema="tenant_test"
        )

        # Path should be in temp_uploads with job_uuid
        assert "tenant_test/temp_uploads/" in relative_path
        assert job_uuid in relative_path

        # File should exist and have correct content
        full_path = file_storage.base_path / relative_path
        assert full_path.exists()
        assert full_path.read_bytes() == b"temp file content"

    def test_move_from_temp(self, file_storage):
        """move_from_temp should move file from temp to permanent storage."""
        # Step 1: Create temp file
        file_content = BytesIO(b"document to move")
        job_uuid = "move-test-uuid"

        temp_path = file_storage.save_temp_file(
            file=file_content,
            job_uuid=job_uuid,
            filename="document.pdf",
            tenant_schema="tenant_test"
        )

        temp_full_path = file_storage.base_path / temp_path
        assert temp_full_path.exists()

        # Step 2: Move to permanent storage
        permanent_path = file_storage.move_from_temp(
            temp_relative_path=temp_path,
            entity_type="SOGGETTO_ANAGRAFICO",
            entity_id=123,
            tenant_schema="tenant_test"
        )

        # Permanent file should exist
        permanent_full_path = file_storage.base_path / permanent_path
        assert permanent_full_path.exists()
        assert permanent_full_path.read_bytes() == b"document to move"

        # Temp file should be removed
        assert not temp_full_path.exists()

        # Path should be in correct location
        assert "tenant_test/soggetto_anagrafico/123/" in permanent_path
        assert "temp_uploads" not in permanent_path

    def test_move_from_temp_nonexistent_file(self, file_storage):
        """move_from_temp should raise error for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            file_storage.move_from_temp(
                temp_relative_path="tenant_test/temp_uploads/fake/file.txt",
                entity_type="entity",
                entity_id=1,
                tenant_schema="tenant_test"
            )

    def test_move_from_temp_security_validation(self, file_storage):
        """move_from_temp should validate paths for security."""
        # Create temp file
        file_content = BytesIO(b"test")
        temp_path = file_storage.save_temp_file(
            file=file_content,
            job_uuid="security-test",
            filename="test.txt",
            tenant_schema="tenant_test"
        )

        # Try to move with invalid tenant (should fail validation)
        with pytest.raises(ValueError):
            file_storage.move_from_temp(
                temp_relative_path=temp_path,
                entity_type="entity",
                entity_id=1,
                tenant_schema="tenant_other"  # Different tenant!
            )


class TestFileOperations:
    """Test basic file operations with tenant awareness."""

    def test_get_file_path_with_tenant(self, file_storage):
        """get_file_path should resolve correctly with tenant_schema."""
        # Create file
        file_content = BytesIO(b"test")
        relative_path = file_storage.save_file(
            file=file_content,
            entity_type="entity",
            entity_id=1,
            filename="test.txt",
            tenant_schema="tenant_test"
        )

        # Get full path with tenant validation
        full_path = file_storage.get_file_path(relative_path, tenant_schema="tenant_test")

        assert full_path.exists()
        assert full_path.read_bytes() == b"test"

    def test_delete_file_with_tenant(self, file_storage):
        """delete_file should work with tenant_schema."""
        # Create file
        file_content = BytesIO(b"to delete")
        relative_path = file_storage.save_file(
            file=file_content,
            entity_type="entity",
            entity_id=1,
            filename="delete_me.txt",
            tenant_schema="tenant_test"
        )

        full_path = file_storage.base_path / relative_path
        assert full_path.exists()

        # Delete
        success = file_storage.delete_file(relative_path, tenant_schema="tenant_test")
        assert success
        assert not full_path.exists()

    def test_get_file_size_with_tenant(self, file_storage):
        """get_file_size should return correct size with tenant_schema."""
        content = b"12345678"  # 8 bytes
        file_content = BytesIO(content)

        relative_path = file_storage.save_file(
            file=file_content,
            entity_type="entity",
            entity_id=1,
            filename="size_test.txt",
            tenant_schema="tenant_test"
        )

        size = file_storage.get_file_size(relative_path, tenant_schema="tenant_test")
        assert size == len(content)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_save_file_without_tenant_raises_error(self, file_storage):
        """Saving file without tenant_schema should raise error."""
        file_content = BytesIO(b"test")

        with pytest.raises(TypeError):
            # Missing required tenant_schema argument
            file_storage.save_file(
                file=file_content,
                entity_type="entity",
                entity_id=1,
                filename="test.txt"
            )

    def test_large_entity_id(self, file_storage):
        """Should handle large entity IDs."""
        file_content = BytesIO(b"test")

        relative_path = file_storage.save_file(
            file=file_content,
            entity_type="entity",
            entity_id=999999999,
            filename="test.txt",
            tenant_schema="tenant_test"
        )

        assert "999999999" in relative_path

    def test_special_characters_in_filename(self, file_storage):
        """Should handle special characters in filename."""
        file_content = BytesIO(b"test")

        # Original filename with special chars
        relative_path = file_storage.save_file(
            file=file_content,
            entity_type="entity",
            entity_id=1,
            filename="my file (v2) [final].txt",
            tenant_schema="tenant_test"
        )

        # Should create file with UUID name but preserve extension
        assert relative_path.endswith(".txt")
        full_path = file_storage.base_path / relative_path
        assert full_path.exists()
