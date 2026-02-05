"""
Pytest Configuration and Fixtures.

Shared fixtures for all tests.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from scout.main import app
from scout.modules import module_registry


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client for testing API endpoints.

    Usage:
        async def test_health(client):
            response = await client.get("/api/v1/health")
            assert response.status_code == 200
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def clean_module_registry() -> Generator[None, None, None]:
    """Clean module registry between tests."""
    yield
    module_registry.clear()


@pytest.fixture
def sample_threat_data() -> dict[str, Any]:
    """Sample threat data for testing."""
    return {
        "title": "Test Port Scan Detected",
        "threat_type": "port_scan",
        "severity": "high",
        "description": "Multiple port scan attempts from suspicious IP",
        "source_ip": "192.168.1.100",
        "target_ip": "10.0.0.1",
    }


@pytest.fixture
def sample_asset_data() -> dict[str, Any]:
    """Sample asset data for testing."""
    return {
        "name": "Test Server",
        "hostname": "test-server-01",
        "ip_address": "10.0.0.1",
        "asset_type": "server",
        "criticality": 4,
    }
