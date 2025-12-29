"""Pytest configuration and fixtures."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from nexus_cli.client import NexusClient
from nexus_cli.config import Settings


@pytest.fixture
def mock_settings():
    """Provide mock settings for testing."""
    return Settings(
        host="https://nexus.example.com",
        username="testuser",
        password="testpass",
        timeout=30,
        verify_ssl=True,
    )


@pytest.fixture
def mock_client(mock_settings):
    """Provide mock NexusClient for testing."""
    client = MagicMock(spec=NexusClient)
    client.base_url = mock_settings.host
    client.timeout = mock_settings.timeout
    return client


@pytest.fixture
def sample_component():
    """Provide sample component data."""
    return {
        "id": "test-component-id",
        "repository": "maven-releases",
        "format": "maven2",
        "group": "com.example",
        "name": "myapp",
        "version": "1.0.0",
        "assets": [
            {
                "id": "asset-1",
                "path": "com/example/myapp/1.0.0/myapp-1.0.0.jar",
                "downloadUrl": "https://nexus.example.com/repository/maven-releases/com/example/myapp/1.0.0/myapp-1.0.0.jar",
                "fileSize": 1024000,
                "checksum": {
                    "sha1": "abc123",
                    "sha256": "def456",
                },
            }
        ],
    }


@pytest.fixture
def sample_asset():
    """Provide sample asset data."""
    return {
        "id": "asset-1",
        "repository": "raw-hosted",
        "format": "raw",
        "path": "/data/file.txt",
        "downloadUrl": "https://nexus.example.com/repository/raw-hosted/data/file.txt",
        "fileSize": 2048,
        "contentType": "text/plain",
        "checksum": {
            "sha1": "abc123",
            "md5": "def456",
        },
    }


async def async_iterator(items):
    """Helper to create async iterator from list."""
    for item in items:
        yield item
