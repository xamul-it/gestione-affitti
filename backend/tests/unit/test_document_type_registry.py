"""
Unit tests for DocumentTypeRegistry.

Tests:
- Registration from manifest
- Lookup by full key, codice, module
- Inheritance between modules
- Category and parsing service indexing
"""
import pytest
from app.core.platform_services.document_type_registry import (
    DocumentTypeRegistry,
    DocumentTypeDefinition
)


@pytest.fixture
def registry():
    """Create fresh registry instance for each test."""
    reg = DocumentTypeRegistry()
    reg.clear()  # Clear any existing data
    return reg


@pytest.fixture
def sample_manifest_anagrafica():
    """Sample manifest for anagrafica_italiana module."""
    return {
        "name": "Anagrafica Italiana",
        "technical_name": "anagrafica_italiana",
        "document_types": [
            {
                "codice": "CARTA_IDENTITA",
                "nome": "Carta d'Identità",
                "categoria": "identita",
                "richiede_scadenza": True,
                "parsing_service": "mrz",
                "parsing_config": {
                    "mrz_format": "td1",
                    "rotate_mode": "auto"
                }
            },
            {
                "codice": "PASSAPORTO",
                "nome": "Passaporto",
                "categoria": "identita",
                "richiede_scadenza": True,
                "parsing_service": "mrz",
                "parsing_config": {
                    "mrz_format": "td3"
                }
            },
            {
                "codice": "CODICE_FISCALE",
                "nome": "Tessera Codice Fiscale",
                "categoria": "identita",
                "richiede_scadenza": False
            }
        ]
    }


@pytest.fixture
def sample_manifest_contratti():
    """Sample manifest for contratti module."""
    return {
        "name": "Contratti",
        "technical_name": "contratti",
        "document_types": [
            {
                "codice": "CONTRATTO_LOCAZIONE",
                "nome": "Contratto di Locazione",
                "categoria": "contratto",
                "richiede_scadenza": False,
                "parsing_service": "contract_parser",
                "parsing_config": {
                    "extract_dates": True,
                    "extract_parties": True
                }
            }
        ]
    }


class TestRegistration:
    """Test document type registration from manifest."""

    def test_register_from_manifest(self, registry, sample_manifest_anagrafica):
        """Should register all document types from manifest."""
        registry.register_from_manifest("anagrafica_italiana", sample_manifest_anagrafica)

        assert len(registry) == 3
        assert "anagrafica_italiana.CARTA_IDENTITA" in registry
        assert "anagrafica_italiana.PASSAPORTO" in registry
        assert "anagrafica_italiana.CODICE_FISCALE" in registry

    def test_register_multiple_modules(self, registry, sample_manifest_anagrafica, sample_manifest_contratti):
        """Should register types from multiple modules."""
        registry.register_from_manifest("anagrafica_italiana", sample_manifest_anagrafica)
        registry.register_from_manifest("contratti", sample_manifest_contratti)

        assert len(registry) == 4
        assert "anagrafica_italiana.CARTA_IDENTITA" in registry
        assert "contratti.CONTRATTO_LOCAZIONE" in registry

    def test_register_empty_manifest(self, registry):
        """Should handle manifest without document_types."""
        manifest = {
            "name": "Test Module",
            "technical_name": "test_module"
        }

        registry.register_from_manifest("test_module", manifest)
        assert len(registry) == 0

    def test_register_overwrite_warning(self, registry, sample_manifest_anagrafica):
        """Should warn when overwriting existing type."""
        # Register twice
        registry.register_from_manifest("anagrafica_italiana", sample_manifest_anagrafica)
        registry.register_from_manifest("anagrafica_italiana", sample_manifest_anagrafica)

        # Should still have 3 types (not duplicated)
        assert len(registry) == 3


class TestLookup:
    """Test document type lookup methods."""

    def test_get_by_full_key(self, registry, sample_manifest_anagrafica):
        """Should retrieve type by full key."""
        registry.register_from_manifest("anagrafica_italiana", sample_manifest_anagrafica)

        doc_type = registry.get("anagrafica_italiana.CARTA_IDENTITA")

        assert doc_type is not None
        assert doc_type.codice == "CARTA_IDENTITA"
        assert doc_type.nome == "Carta d'Identità"
        assert doc_type.modulo_origine == "anagrafica_italiana"
        assert doc_type.parsing_service == "mrz"

    def test_get_nonexistent(self, registry):
        """Should return None for nonexistent type."""
        doc_type = registry.get("nonexistent.TYPE")
        assert doc_type is None

    def test_get_by_codice_with_module(self, registry, sample_manifest_anagrafica):
        """Should retrieve type by codice and module."""
        registry.register_from_manifest("anagrafica_italiana", sample_manifest_anagrafica)

        doc_type = registry.get_by_codice("PASSAPORTO", modulo="anagrafica_italiana")

        assert doc_type is not None
        assert doc_type.codice == "PASSAPORTO"
        assert doc_type.nome == "Passaporto"

    def test_get_by_codice_without_module(self, registry, sample_manifest_anagrafica):
        """Should find type by codice across all modules."""
        registry.register_from_manifest("anagrafica_italiana", sample_manifest_anagrafica)

        doc_type = registry.get_by_codice("CARTA_IDENTITA")

        assert doc_type is not None
        assert doc_type.codice == "CARTA_IDENTITA"

    def test_get_by_codice_ambiguous(self, registry, sample_manifest_anagrafica, sample_manifest_contratti):
        """Should return first match when codice exists in multiple modules."""
        # Create duplicate codice in different modules
        manifest_duplicate = {
            "technical_name": "module_b",
            "document_types": [
                {
                    "codice": "CARTA_IDENTITA",  # Same as anagrafica
                    "nome": "Different Card",
                    "categoria": "other"
                }
            ]
        }

        registry.register_from_manifest("anagrafica_italiana", sample_manifest_anagrafica)
        registry.register_from_manifest("module_b", manifest_duplicate)

        # Should find one (first registered)
        doc_type = registry.get_by_codice("CARTA_IDENTITA")
        assert doc_type is not None


class TestIndexing:
    """Test indexing by module, category, and parsing service."""

    def test_get_by_module(self, registry, sample_manifest_anagrafica):
        """Should retrieve all types for a module."""
        registry.register_from_manifest("anagrafica_italiana", sample_manifest_anagrafica)

        types = registry.get_by_module("anagrafica_italiana")

        assert len(types) == 3
        assert all(t.modulo_origine == "anagrafica_italiana" for t in types)

    def test_get_by_category(self, registry, sample_manifest_anagrafica, sample_manifest_contratti):
        """Should retrieve all types in a category."""
        registry.register_from_manifest("anagrafica_italiana", sample_manifest_anagrafica)
        registry.register_from_manifest("contratti", sample_manifest_contratti)

        identita_types = registry.get_by_category("identita")
        assert len(identita_types) == 3

        contratto_types = registry.get_by_category("contratto")
        assert len(contratto_types) == 1

    def test_get_types_with_parsing(self, registry, sample_manifest_anagrafica):
        """Should retrieve only types with parsing service."""
        registry.register_from_manifest("anagrafica_italiana", sample_manifest_anagrafica)

        parsing_types = registry.get_types_with_parsing()

        # Only CARTA_IDENTITA and PASSAPORTO have parsing_service
        assert len(parsing_types) == 2
        assert all(t.parsing_service is not None for t in parsing_types)

    def test_get_by_parsing_service(self, registry, sample_manifest_anagrafica, sample_manifest_contratti):
        """Should retrieve all types for a parsing service."""
        registry.register_from_manifest("anagrafica_italiana", sample_manifest_anagrafica)
        registry.register_from_manifest("contratti", sample_manifest_contratti)

        mrz_types = registry.get_by_parsing_service("mrz")
        assert len(mrz_types) == 2
        assert all(t.parsing_service == "mrz" for t in mrz_types)

        contract_types = registry.get_by_parsing_service("contract_parser")
        assert len(contract_types) == 1


class TestDocumentTypeDefinition:
    """Test DocumentTypeDefinition class."""

    def test_full_key_property(self):
        """Should generate correct full key."""
        doc_type = DocumentTypeDefinition(
            codice="TEST",
            nome="Test Document",
            categoria="test",
            modulo_origine="test_module"
        )

        assert doc_type.full_key == "test_module.TEST"

    def test_validation_missing_codice(self):
        """Should raise error if codice missing."""
        with pytest.raises(ValueError, match="codice è obbligatorio"):
            DocumentTypeDefinition(
                codice="",
                nome="Test",
                categoria="test",
                modulo_origine="module"
            )

    def test_validation_missing_nome(self):
        """Should raise error if nome missing."""
        with pytest.raises(ValueError, match="nome è obbligatorio"):
            DocumentTypeDefinition(
                codice="TEST",
                nome="",
                categoria="test",
                modulo_origine="module"
            )

    def test_parsing_config_defaults_to_empty_dict(self):
        """parsing_config should default to empty dict."""
        doc_type = DocumentTypeDefinition(
            codice="TEST",
            nome="Test",
            categoria="test",
            modulo_origine="module",
            parsing_config=None
        )

        assert doc_type.parsing_config == {}


class TestInheritance:
    """Test document type inheritance."""

    def test_inherits_from_field(self, registry):
        """Should store inherits_from relationship."""
        manifest = {
            "technical_name": "custom_module",
            "document_types": [
                {
                    "codice": "CUSTOM_CARTA",
                    "nome": "Custom Carta Identità",
                    "categoria": "identita",
                    "inherits_from": "anagrafica_italiana.CARTA_IDENTITA"
                }
            ]
        }

        registry.register_from_manifest("custom_module", manifest)

        doc_type = registry.get("custom_module.CUSTOM_CARTA")
        assert doc_type.inherits_from == "anagrafica_italiana.CARTA_IDENTITA"


class TestListAndClear:
    """Test list_all and clear methods."""

    def test_list_all(self, registry, sample_manifest_anagrafica):
        """Should list all registered types."""
        registry.register_from_manifest("anagrafica_italiana", sample_manifest_anagrafica)

        all_types = registry.list_all()

        assert len(all_types) == 3
        assert isinstance(all_types, list)
        assert all(isinstance(t, DocumentTypeDefinition) for t in all_types)

    def test_clear(self, registry, sample_manifest_anagrafica):
        """Should clear all registered types."""
        registry.register_from_manifest("anagrafica_italiana", sample_manifest_anagrafica)
        assert len(registry) == 3

        registry.clear()
        assert len(registry) == 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_malformed_document_type(self, registry):
        """Should handle malformed document type gracefully."""
        manifest = {
            "technical_name": "bad_module",
            "document_types": [
                {
                    # Missing required fields
                    "categoria": "test"
                }
            ]
        }

        # Should not crash, just skip invalid entry
        registry.register_from_manifest("bad_module", manifest)

        # Should have registered nothing
        assert len(registry) == 0

    def test_empty_parsing_config(self, registry):
        """Should handle empty parsing_config."""
        manifest = {
            "technical_name": "test_module",
            "document_types": [
                {
                    "codice": "TEST",
                    "nome": "Test",
                    "categoria": "test",
                    "parsing_service": "mrz",
                    "parsing_config": {}  # Empty config
                }
            ]
        }

        registry.register_from_manifest("test_module", manifest)

        doc_type = registry.get("test_module.TEST")
        assert doc_type.parsing_config == {}
