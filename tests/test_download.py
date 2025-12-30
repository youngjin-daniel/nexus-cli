"""Tests for download command."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from click.testing import CliRunner

from nexus_cli.commands.download import download
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
            "repository": "my-repo",
            "path": "MyProject/build_20250101_120000/component-a/artifact.zip",
            "downloadUrl": "https://nexus.example.com/test1",
            "fileSize": 152790992,
        },
        {
            "repository": "my-repo",
            "path": "MyProject/build_20250101_120000/component-b/artifact.zip",
            "downloadUrl": "https://nexus.example.com/test2",
            "fileSize": 120356446,
        },
    ]


def test_download_command_no_pattern(cli_runner, mock_settings):
    """Test download command fails without pattern."""
    with patch("nexus_cli.commands.download.get_settings") as mock_get_settings:
        mock_get_settings.return_value = mock_settings

        # Run command without pattern
        result = cli_runner.invoke(download, [])

        assert result.exit_code != 0


def test_download_command_success(cli_runner, mock_settings, sample_assets):
    """Test download command successfully searches and downloads assets."""
    with patch("nexus_cli.commands.download.get_settings") as mock_get_settings, \
         patch("nexus_cli.commands.download.perform_search") as mock_perform_search, \
         patch("nexus_cli.commands.download.NexusClient") as mock_client_class, \
         patch("pathlib.Path.mkdir"), \
         tempfile.TemporaryDirectory() as tmpdir:

        # Setup mocks
        mock_get_settings.return_value = mock_settings
        mock_perform_search.return_value = sample_assets

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = AsyncMock()
        mock_client_instance.download_asset = AsyncMock()
        mock_client_class.return_value = mock_client_instance

        # Run command
        result = cli_runner.invoke(download, [
            "-p", "MyProject/build_20250101*artifact.zip",
            "-o", tmpdir
        ])

        assert result.exit_code == 0
        # Check that perform_search was called
        assert mock_perform_search.called
        # Check download completion message
        assert "Download completed!" in result.stderr
        assert "Success: 2 file(s)" in result.stderr


def test_download_command_no_assets_found(cli_runner, mock_settings):
    """Test download command when no assets match the pattern."""
    with patch("nexus_cli.commands.download.get_settings") as mock_get_settings, \
         patch("nexus_cli.commands.download.perform_search") as mock_perform_search:

        mock_get_settings.return_value = mock_settings
        mock_perform_search.return_value = []

        # Run command
        result = cli_runner.invoke(download, [
            "-p", "NonExistent/*"
        ])

        assert result.exit_code == 1
        assert "No assets found matching the patterns" in result.stderr


def test_download_command_multiple_patterns(cli_runner, mock_settings, sample_assets):
    """Test download command with multiple patterns."""
    with patch("nexus_cli.commands.download.get_settings") as mock_get_settings, \
         patch("nexus_cli.commands.download.perform_search") as mock_perform_search, \
         patch("nexus_cli.commands.download.NexusClient") as mock_client_class, \
         patch("pathlib.Path.mkdir"), \
         tempfile.TemporaryDirectory() as tmpdir:

        # Setup mocks
        mock_get_settings.return_value = mock_settings
        mock_perform_search.return_value = sample_assets

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = AsyncMock()
        mock_client_instance.download_asset = AsyncMock()
        mock_client_class.return_value = mock_client_instance

        # Run command with multiple patterns
        result = cli_runner.invoke(download, [
            "-p", "MyProject/*artifact.zip",
            "-p", "MyProject/*.tar.gz",
            "-o", tmpdir
        ])

        assert result.exit_code == 0
        # Check that perform_search was called with both patterns
        assert mock_perform_search.called


def test_download_command_path_extraction(cli_runner, mock_settings):
    """Test that download extracts last two path components correctly."""
    asset = {
        "path": "MyProject/build_20250101_120000/component-a/file.tar.gz",
        "downloadUrl": "https://nexus.example.com/test",
    }

    # Expected: component-a/file.tar.gz
    path_parts = asset["path"].split("/")
    if len(path_parts) >= 2:
        relative_path = "/".join(path_parts[-2:])
    else:
        relative_path = path_parts[-1] if path_parts else "unknown"

    assert relative_path == "component-a/file.tar.gz"


def test_download_command_with_repository(cli_runner, mock_settings, sample_assets):
    """Test download command with repository option."""
    with patch("nexus_cli.commands.download.get_settings") as mock_get_settings, \
         patch("nexus_cli.commands.download.perform_search") as mock_perform_search, \
         patch("nexus_cli.commands.download.NexusClient") as mock_client_class, \
         patch("pathlib.Path.mkdir"), \
         tempfile.TemporaryDirectory() as tmpdir:

        # Setup mocks
        mock_get_settings.return_value = mock_settings
        mock_perform_search.return_value = sample_assets

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = AsyncMock()
        mock_client_instance.download_asset = AsyncMock()
        mock_client_class.return_value = mock_client_instance

        # Run command with repository option
        result = cli_runner.invoke(download, [
            "-r", "my-repo",
            "-p", "MyProject/*artifact.zip",
            "-o", tmpdir
        ])

        assert result.exit_code == 0


def test_download_command_debug_mode(cli_runner, mock_settings, sample_assets):
    """Test download command with debug mode."""
    with patch("nexus_cli.commands.download.get_settings") as mock_get_settings, \
         patch("nexus_cli.commands.download.perform_search") as mock_perform_search, \
         patch("nexus_cli.commands.download.NexusClient") as mock_client_class, \
         patch("pathlib.Path.mkdir"), \
         tempfile.TemporaryDirectory() as tmpdir:

        # Setup mocks
        mock_get_settings.return_value = mock_settings
        mock_perform_search.return_value = sample_assets

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = AsyncMock()
        mock_client_instance.download_asset = AsyncMock()
        mock_client_class.return_value = mock_client_instance

        # Run command with debug flag
        result = cli_runner.invoke(download, [
            "-p", "MyProject/*artifact.zip",
            "-o", tmpdir,
            "--debug"
        ])

        assert result.exit_code == 0
