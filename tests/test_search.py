"""Tests for search command."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch, mock_open

import pytest
from click.testing import CliRunner

from nexus_cli.commands.search import search
from tests.conftest import async_iterator


@pytest.fixture
def cli_runner():
    """Provide Click CLI runner."""
    return CliRunner()


@pytest.fixture
def sample_assets():
    """Sample assets for testing."""
    return [
        {
            "id": "test1",
            "repository": "my-repo",
            "path": "MyProject/build_20250101_120000/component-a/artifact.zip",
            "downloadUrl": "https://nexus.example.com/test1",
            "fileSize": 152790992,
        },
        {
            "id": "test2",
            "repository": "my-repo",
            "path": "MyProject/build_20250101_120000/component-b/artifact.zip",
            "downloadUrl": "https://nexus.example.com/test2",
            "fileSize": 120356446,
        },
    ]


def test_search_command_success(cli_runner, mock_settings, sample_assets):
    """Test search command successfully saves results to JSON."""
    with patch("nexus_cli.commands.search.get_settings") as mock_get_settings, \
         patch("nexus_cli.commands.search.NexusClient") as mock_client_class, \
         patch("builtins.open", mock_open()) as mock_file, \
         patch("pathlib.Path.mkdir"):

        # Setup mocks
        mock_get_settings.return_value = mock_settings
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = AsyncMock()

        # Mock search_assets to return sample data
        async def mock_search_assets(**kwargs):
            async for item in async_iterator(sample_assets):
                yield item

        mock_client_instance.search_assets = mock_search_assets
        mock_client_class.return_value = mock_client_instance

        # Run command
        result = cli_runner.invoke(search, [
            "--repository", "my-repo",
            "--pattern", "MyProject/build_20250101*artifact.zip"
        ])

        assert result.exit_code == 0
        assert "Search started" in result.output
        assert "Search completed!" in result.output


def test_search_command_no_pattern(cli_runner, mock_settings):
    """Test search command fails without pattern."""
    with patch("nexus_cli.commands.search.get_settings") as mock_get_settings:
        mock_get_settings.return_value = mock_settings

        # Run command without pattern
        result = cli_runner.invoke(search, ["--repository", "my-repo"])

        assert result.exit_code != 0


def test_search_command_multiple_patterns(cli_runner, mock_settings, sample_assets):
    """Test search command with multiple patterns."""
    with patch("nexus_cli.commands.search.get_settings") as mock_get_settings, \
         patch("nexus_cli.commands.search.NexusClient") as mock_client_class, \
         patch("builtins.open", mock_open()) as mock_file, \
         patch("pathlib.Path.mkdir"):

        # Setup mocks
        mock_get_settings.return_value = mock_settings
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = AsyncMock()

        # Mock search_assets
        async def mock_search_assets(**kwargs):
            async for item in async_iterator(sample_assets):
                yield item

        mock_client_instance.search_assets = mock_search_assets
        mock_client_class.return_value = mock_client_instance

        # Run command with multiple patterns
        result = cli_runner.invoke(search, [
            "--repository", "my-repo",
            "--pattern", "MyProject/*artifact.zip",
            "--pattern", "MyProject/*.tar.gz"
        ])

        assert result.exit_code == 0
        assert "Search started" in result.output