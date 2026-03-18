"""
Integration tests for Soggetti API endpoints.

Tests the complete API stack with database.
"""

import pytest
from datetime import date

from modules.anagrafica_italiana.models import SoggettoAnagrafico


@pytest.mark.integration
@pytest.mark.module_anagrafica
class TestSoggettiCRUDAPI:
    """Test CRUD operations for Soggetti API."""

    def test_create_soggetto_persona_fisica(self, auth_client, tenant_db_session):
        """Should create new persona fisica successfully."""
        # Arrange
        payload = {
            "tipo_soggetto": "PERSONA_FISICA",
            "nome": "Mario",
            "cognome": "Rossi",
            "codice_fiscale": "RSSMRA80A01H501Z",
            "data_nascita": "1980-01-01",
            "luogo_nascita": "Roma",
            "email": "mario.rossi@example.com",
        }

        # Act
        response = auth_client.post("/api/v1/anagrafica/soggetti/", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["nome"] == "Mario"
        assert data["cognome"] == "Rossi"
        assert data["codice_fiscale"] == "RSSMRA80A01H501Z"
        assert "id" in data

        # Verify in database
        soggetto = tenant_db_session.query(SoggettoAnagrafico).filter_by(
            codice_fiscale="RSSMRA80A01H501Z"
        ).first()
        assert soggetto is not None
        assert soggetto.nome == "Mario"

    def test_create_soggetto_duplicate_codice_fiscale_fails(self, auth_client, tenant_db_session):
        """Should reject duplicate codice fiscale."""
        # Arrange - create first soggetto
        first_payload = {
            "tipo_soggetto": "PERSONA_FISICA",
            "nome": "Mario",
            "cognome": "Rossi",
            "codice_fiscale": "RSSMRA80A01H501Z",
        }
        auth_client.post("/api/v1/anagrafica/soggetti/", json=first_payload)

        # Act - try to create duplicate
        duplicate_payload = {
            "tipo_soggetto": "PERSONA_FISICA",
            "nome": "Luigi",
            "cognome": "Verdi",
            "codice_fiscale": "RSSMRA80A01H501Z",  # Same CF
        }
        response = auth_client.post("/api/v1/anagrafica/soggetti/", json=duplicate_payload)

        # Assert
        assert response.status_code == 400
        assert "codice fiscale" in response.json()["detail"].lower()

    def test_list_soggetti_returns_all(self, auth_client, tenant_db_session):
        """Should list all soggetti for the tenant."""
        # Arrange - create test soggetti
        soggetto1 = SoggettoAnagrafico(
            tipo_soggetto="PERSONA_FISICA",
            nome="Mario",
            cognome="Rossi",
            codice_fiscale="RSSMRA80A01H501Z",
        )
        soggetto2 = SoggettoAnagrafico(
            tipo_soggetto="PERSONA_FISICA",
            nome="Luigi",
            cognome="Bianchi",
            codice_fiscale="BNCLGU85M15H501Y",
        )
        tenant_db_session.add(soggetto1)
        tenant_db_session.add(soggetto2)
        tenant_db_session.commit()

        # Act
        response = auth_client.get("/api/v1/anagrafica/soggetti/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(s["nome"] == "Mario" for s in data)
        assert any(s["nome"] == "Luigi" for s in data)

    def test_get_soggetto_by_id(self, auth_client, tenant_db_session):
        """Should retrieve specific soggetto by ID."""
        # Arrange
        soggetto = SoggettoAnagrafico(
            tipo_soggetto="PERSONA_FISICA",
            nome="Mario",
            cognome="Rossi",
            codice_fiscale="RSSMRA80A01H501Z",
        )
        tenant_db_session.add(soggetto)
        tenant_db_session.commit()
        tenant_db_session.refresh(soggetto)

        # Act
        response = auth_client.get(f"/api/v1/anagrafica/soggetti/{soggetto.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == soggetto.id
        assert data["nome"] == "Mario"

    def test_update_soggetto(self, auth_client, tenant_db_session):
        """Should update soggetto successfully."""
        # Arrange
        soggetto = SoggettoAnagrafico(
            tipo_soggetto="PERSONA_FISICA",
            nome="Mario",
            cognome="Rossi",
            codice_fiscale="RSSMRA80A01H501Z",
        )
        tenant_db_session.add(soggetto)
        tenant_db_session.commit()
        tenant_db_session.refresh(soggetto)

        # Act
        update_payload = {
            "email": "new.email@example.com",
            "telefono": "+39 123 456 7890",
        }
        response = auth_client.put(
            f"/api/v1/anagrafica/soggetti/{soggetto.id}",
            json=update_payload
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "new.email@example.com"
        assert data["telefono"] == "+39 123 456 7890"

        # Verify in database
        tenant_db_session.refresh(soggetto)
        assert soggetto.email == "new.email@example.com"

    def test_delete_soggetto(self, auth_client, tenant_db_session):
        """Should delete soggetto successfully."""
        # Arrange
        soggetto = SoggettoAnagrafico(
            tipo_soggetto="PERSONA_FISICA",
            nome="Mario",
            cognome="Rossi",
            codice_fiscale="RSSMRA80A01H501Z",
        )
        tenant_db_session.add(soggetto)
        tenant_db_session.commit()
        soggetto_id = soggetto.id

        # Act
        response = auth_client.delete(f"/api/v1/anagrafica/soggetti/{soggetto_id}")

        # Assert
        assert response.status_code == 200

        # Verify deletion
        deleted = tenant_db_session.query(SoggettoAnagrafico).filter_by(
            id=soggetto_id
        ).first()
        assert deleted is None


@pytest.mark.integration
@pytest.mark.module_anagrafica
class TestFindSimilarAPI:
    """Test find-similar endpoint for duplicate detection."""

    def test_find_similar_exact_cf_match(self, auth_client, tenant_db_session):
        """Should find exact codice fiscale match with 100% score."""
        # Arrange - create existing soggetto
        existing = SoggettoAnagrafico(
            tipo_soggetto="PERSONA_FISICA",
            nome="Mario",
            cognome="Rossi",
            codice_fiscale="RSSMRA80A01H501Z",
            data_nascita=date(1980, 1, 1),
        )
        tenant_db_session.add(existing)
        tenant_db_session.commit()

        # Act - search for similar with same CF
        response = auth_client.post(
            "/api/v1/anagrafica/soggetti/find-similar",
            json={"codice_fiscale": "RSSMRA80A01H501Z"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["candidates"][0]["similarity_score"] == 1.0
        assert data["candidates"][0]["match_quality"] == "perfect"
        assert data["candidates"][0]["recommended_action"] == "USE_EXISTING"

    def test_find_similar_fuzzy_name_match(self, auth_client, tenant_db_session):
        """Should find fuzzy name matches."""
        # Arrange - create similar soggetto
        similar = SoggettoAnagrafico(
            tipo_soggetto="PERSONA_FISICA",
            nome="Mario",
            cognome="Rossi",
            data_nascita=date(1980, 1, 1),
        )
        tenant_db_session.add(similar)
        tenant_db_session.commit()

        # Act - search with exact same name and DOB
        response = auth_client.post(
            "/api/v1/anagrafica/soggetti/find-similar",
            json={
                "nome": "Mario",
                "cognome": "Rossi",
                "data_nascita": "1980-01-01"
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        # With exact name and DOB match, score should be very high
        assert data["candidates"][0]["similarity_score"] >= 0.95

    def test_find_similar_no_matches(self, auth_client, tenant_db_session):
        """Should return empty list when no matches found."""
        # Act - search for non-existent person
        response = auth_client.post(
            "/api/v1/anagrafica/soggetti/find-similar",
            json={
                "nome": "NonExistent",
                "cognome": "Person",
                "codice_fiscale": "XXXYYY00A00Z000Z"
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["candidates"] == []

    def test_find_similar_with_threshold(self, auth_client, tenant_db_session):
        """Should filter results by threshold."""
        # Arrange - create soggetto with similar but not exact data
        similar = SoggettoAnagrafico(
            tipo_soggetto="PERSONA_FISICA",
            nome="Mario",
            cognome="Rossi",
            data_nascita=date(1985, 6, 15),  # Different DOB
        )
        tenant_db_session.add(similar)
        tenant_db_session.commit()

        # Act - search with high threshold
        response = auth_client.post(
            "/api/v1/anagrafica/soggetti/find-similar",
            json={
                "nome": "Mario",
                "cognome": "Rossi",
                "data_nascita": "1980-01-01",
                "threshold": 0.90  # High threshold
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Different DOB should result in score < 0.90, so no matches
        assert data["total"] == 0

    def test_find_similar_exclude_id(self, auth_client, tenant_db_session):
        """Should exclude specified ID from results."""
        # Arrange
        soggetto = SoggettoAnagrafico(
            tipo_soggetto="PERSONA_FISICA",
            nome="Mario",
            cognome="Rossi",
            codice_fiscale="RSSMRA80A01H501Z",
        )
        tenant_db_session.add(soggetto)
        tenant_db_session.commit()

        # Act - exclude the only match
        response = auth_client.post(
            "/api/v1/anagrafica/soggetti/find-similar",
            json={
                "codice_fiscale": "RSSMRA80A01H501Z",
                "exclude_id": soggetto.id
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0


@pytest.mark.integration
@pytest.mark.module_anagrafica
@pytest.mark.tenant
class TestSoggettiTenantIsolation:
    """Test tenant isolation for soggetti."""

    def test_list_soggetti_only_shows_own_tenant(
        self,
        auth_client,
        another_tenant_client,
        tenant_db_session
    ):
        """Each tenant should only see their own soggetti."""
        # Arrange - create soggetto for tenant A
        soggetto_a = SoggettoAnagrafico(
            tipo_soggetto="PERSONA_FISICA",
            nome="Tenant A User",
            cognome="Rossi",
            codice_fiscale="RSSMRA80A01H501Z",
        )
        tenant_db_session.add(soggetto_a)
        tenant_db_session.commit()

        # Act - tenant A can see their soggetto
        response_a = auth_client.get("/api/v1/anagrafica/soggetti/")
        assert response_a.status_code == 200
        data_a = response_a.json()
        assert len(data_a) >= 1
        assert any(s["nome"] == "Tenant A User" for s in data_a)

        # Act - tenant B sees nothing
        response_b = another_tenant_client.get("/api/v1/anagrafica/soggetti/")
        assert response_b.status_code == 200
        data_b = response_b.json()
        # Tenant B should not see tenant A's soggetto
        assert not any(s["nome"] == "Tenant A User" for s in data_b)

    def test_get_soggetto_cross_tenant_returns_404(
        self,
        auth_client,
        another_tenant_client,
        tenant_db_session
    ):
        """Accessing another tenant's soggetto should return 404."""
        # Arrange - create soggetto for tenant A
        soggetto_a = SoggettoAnagrafico(
            tipo_soggetto="PERSONA_FISICA",
            nome="Tenant A User",
            cognome="Rossi",
        )
        tenant_db_session.add(soggetto_a)
        tenant_db_session.commit()

        # Act - tenant B tries to access tenant A's soggetto
        response = another_tenant_client.get(
            f"/api/v1/anagrafica/soggetti/{soggetto_a.id}"
        )

        # Assert - should not find it
        assert response.status_code == 404
