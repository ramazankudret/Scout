"""
Integration Tests for API Endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoints:
    """Tests for health check endpoints."""

    async def test_health_check(self, client: AsyncClient) -> None:
        """Test basic health check."""
        response = await client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Scout"

    async def test_readiness_check(self, client: AsyncClient) -> None:
        """Test readiness check."""
        response = await client.get("/api/v1/ready")

        assert response.status_code == 200
        data = response.json()
        assert "checks" in data


@pytest.mark.asyncio
class TestModulesEndpoints:
    """Tests for modules API endpoints."""

    async def test_list_modules(self, client: AsyncClient) -> None:
        """Test listing modules."""
        response = await client.get("/api/v1/modules")

        assert response.status_code == 200
        data = response.json()
        assert "modules" in data
        assert "count" in data

    async def test_get_nonexistent_module(self, client: AsyncClient) -> None:
        """Test getting a module that doesn't exist."""
        response = await client.get("/api/v1/modules/nonexistent")

        assert response.status_code == 404


@pytest.mark.asyncio
class TestThreatsEndpoints:
    """Tests for threats API endpoints."""

    async def test_list_threats_empty(self, client: AsyncClient) -> None:
        """Test listing threats when empty."""
        response = await client.get("/api/v1/threats")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 0

    async def test_create_threat(
        self, client: AsyncClient, sample_threat_data: dict
    ) -> None:
        """Test creating a threat."""
        response = await client.post("/api/v1/threats", json=sample_threat_data)

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Threat created"
        assert data["threat"]["title"] == sample_threat_data["title"]

    async def test_get_threat_not_found(self, client: AsyncClient) -> None:
        """Test getting a threat that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/v1/threats/{fake_id}")

        assert response.status_code == 404

    async def test_threat_stats(self, client: AsyncClient) -> None:
        """Test getting threat statistics."""
        response = await client.get("/api/v1/threats/stats/summary")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_severity" in data
