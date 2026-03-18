"""
Unit tests for Similarity Matching Service.

Tests the core algorithm logic without database dependencies.
"""

import pytest
from datetime import date
from unittest.mock import Mock, MagicMock

from modules.anagrafica_italiana.services.similarity_matching_service import SimilarityMatchingService
from modules.anagrafica_italiana.models import SoggettoAnagrafico


@pytest.mark.unit
@pytest.mark.module_anagrafica
class TestSimilarityMatchingService:
    """Test suite for SimilarityMatchingService."""

    def test_exact_codice_fiscale_match_returns_100_percent(self):
        """Exact codice fiscale match should return 100% similarity."""
        # Arrange
        mock_db = Mock()
        service = SimilarityMatchingService(mock_db)

        # Create mock soggetto
        mock_soggetto = Mock(spec=SoggettoAnagrafico)
        mock_soggetto.id = 1
        mock_soggetto.codice_fiscale = "RSSMRA80A01H501Z"
        mock_soggetto.nome = "Mario"
        mock_soggetto.cognome = "Rossi"

        # Mock query to return the exact match
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_soggetto
        mock_db.query.return_value = mock_query

        # Act
        candidates = service.find_similar(
            codice_fiscale="RSSMRA80A01H501Z"
        )

        # Assert
        assert len(candidates) == 1
        assert candidates[0]["similarity_score"] == 1.0
        assert candidates[0]["soggetto_id"] == 1
        assert "codice_fiscale" in candidates[0]["match_fields"]

    def test_similar_names_with_exact_dob_high_score(self):
        """Similar names with exact date of birth should score high."""
        # Arrange
        mock_db = Mock()
        service = SimilarityMatchingService(mock_db)

        # Create mock soggetto with similar name
        mock_soggetto = Mock(spec=SoggettoAnagrafico)
        mock_soggetto.id = 2
        mock_soggetto.codice_fiscale = None
        mock_soggetto.nome = "Mario"
        mock_soggetto.cognome = "Rossi"
        mock_soggetto.data_nascita = date(1980, 1, 1)

        # Mock query
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None  # No CF match
        mock_query.filter.return_value.all.return_value = [mock_soggetto]
        mock_db.query.return_value = mock_query

        # Act
        candidates = service.find_similar(
            nome="Mario",
            cognome="Rossi",
            data_nascita=date(1980, 1, 1)
        )

        # Assert
        assert len(candidates) >= 1
        # With exact name and DOB match, score should be very high
        # (nome: 1.0 * 0.3) + (cognome: 1.0 * 0.3) + (dob: 1.0 * 0.4) = 1.0
        assert candidates[0]["similarity_score"] >= 0.95

    def test_typo_in_name_still_matches_with_lower_score(self):
        """Small typo in name should still match with slightly lower score."""
        # Arrange
        mock_db = Mock()
        service = SimilarityMatchingService(mock_db)

        # Create mock soggetto with typo
        mock_soggetto = Mock(spec=SoggettoAnagrafico)
        mock_soggetto.id = 3
        mock_soggetto.codice_fiscale = None
        mock_soggetto.nome = "Mairo"  # Typo: Mario -> Mairo
        mock_soggetto.cognome = "Rossi"
        mock_soggetto.data_nascita = date(1980, 1, 1)

        # Mock query
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_query.filter.return_value.all.return_value = [mock_soggetto]
        mock_db.query.return_value = mock_query

        # Act
        candidates = service.find_similar(
            nome="Mario",
            cognome="Rossi",
            data_nascita=date(1980, 1, 1)
        )

        # Assert
        assert len(candidates) >= 1
        # Score should be slightly lower due to typo, but still high
        assert 0.80 <= candidates[0]["similarity_score"] < 1.0

    def test_different_dob_lowers_score_significantly(self):
        """Different date of birth should lower similarity score significantly."""
        # Arrange
        mock_db = Mock()
        service = SimilarityMatchingService(mock_db)

        mock_soggetto = Mock(spec=SoggettoAnagrafico)
        mock_soggetto.id = 4
        mock_soggetto.codice_fiscale = None
        mock_soggetto.nome = "Mario"
        mock_soggetto.cognome = "Rossi"
        mock_soggetto.data_nascita = date(1985, 6, 15)  # Different year

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_query.filter.return_value.all.return_value = [mock_soggetto]
        mock_db.query.return_value = mock_query

        # Act
        candidates = service.find_similar(
            nome="Mario",
            cognome="Rossi",
            data_nascita=date(1980, 1, 1)
        )

        # Assert
        # DOB weight is 40%, so even with exact names (60%), max score is 0.6
        assert candidates[0]["similarity_score"] <= 0.60

    def test_threshold_filtering_works(self):
        """Only candidates above threshold should be returned."""
        # Arrange
        mock_db = Mock()
        service = SimilarityMatchingService(mock_db)

        # Create mock soggetto with low similarity
        mock_soggetto = Mock(spec=SoggettoAnagrafico)
        mock_soggetto.id = 5
        mock_soggetto.codice_fiscale = None
        mock_soggetto.nome = "Giovanni"  # Very different from "Mario"
        mock_soggetto.cognome = "Bianchi"  # Very different from "Rossi"
        mock_soggetto.data_nascita = date(1990, 12, 31)  # Different DOB

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_query.filter.return_value.all.return_value = [mock_soggetto]
        mock_db.query.return_value = mock_query

        # Act
        candidates = service.find_similar(
            nome="Mario",
            cognome="Rossi",
            data_nascita=date(1980, 1, 1),
            threshold=0.70  # High threshold
        )

        # Assert
        # With completely different names and DOB, score should be very low
        # and filtered out by threshold
        assert len(candidates) == 0

    def test_exclude_id_parameter_works(self):
        """exclude_id parameter should exclude specified ID from results."""
        # Arrange
        mock_db = Mock()
        service = SimilarityMatchingService(mock_db)

        mock_soggetto = Mock(spec=SoggettoAnagrafico)
        mock_soggetto.id = 6
        mock_soggetto.codice_fiscale = "RSSMRA80A01H501Z"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_soggetto
        mock_db.query.return_value = mock_query

        # Act
        candidates = service.find_similar(
            codice_fiscale="RSSMRA80A01H501Z",
            exclude_id=6  # Exclude the only match
        )

        # Assert
        assert len(candidates) == 0

    def test_get_match_quality_classification(self):
        """Test match quality classification logic."""
        # Arrange
        mock_db = Mock()
        service = SimilarityMatchingService(mock_db)

        # Act & Assert
        assert service.get_match_quality(1.0) == "perfect"
        assert service.get_match_quality(0.90) == "high"
        assert service.get_match_quality(0.75) == "medium"
        assert service.get_match_quality(0.55) == "low"

    def test_get_recommended_action_based_on_score(self):
        """Test recommended action based on similarity score."""
        # Arrange
        mock_db = Mock()
        service = SimilarityMatchingService(mock_db)

        # Act & Assert
        assert service.get_recommended_action(1.0) == "USE_EXISTING"
        assert service.get_recommended_action(0.90) == "REVIEW_MANUALLY"
        assert service.get_recommended_action(0.65) == "REVIEW_MANUALLY"
        assert service.get_recommended_action(0.45) == "CREATE_NEW"


@pytest.mark.unit
@pytest.mark.module_anagrafica
@pytest.mark.slow
class TestSimilarityMatchingPerformance:
    """Performance tests for similarity matching (marked as slow)."""

    def test_large_candidate_list_performance(self):
        """Service should handle large candidate lists efficiently."""
        # This test would mock a large dataset and measure performance
        # For now, it's a placeholder showing how to mark slow tests
        pytest.skip("Performance test - implement when needed")
