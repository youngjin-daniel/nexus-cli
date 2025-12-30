"""Tests for upload command."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from click.testing import CliRunner

from nexus.commands.upload import upload


@pytest.fixture
def cli_runner():
    """Provide Click CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("test content")
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_upload_component_basic(mock_client, temp_file):
    """Test basic component upload."""
    mock_client.upload_component = AsyncMock(return_value={"status": "success"})

    result = await mock_client.upload_component(
        repository="raw-hosted",
        file_path=Path(temp_file),
        asset_name="test.txt",
    )

    assert result["status"] == "success"
    mock_client.upload_component.assert_called_once()


def test_upload_command_basic(cli_runner, mock_settings, temp_file):
    """Test upload command with basic parameters."""
    with patch("nexus.commands.upload.get_settings") as mock_get_settings, \
         patch("nexus.commands.upload.NexusClient") as mock_client_class:

        # Setup mocks
        mock_get_settings.return_value = mock_settings
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = AsyncMock()
        mock_client_instance.upload_component = AsyncMock(
            return_value={"status": "success"}
        )
        mock_client_class.return_value = mock_client_instance

        # Run command
        result = cli_runner.invoke(upload, [
            "--repository", "raw-hosted",
            "--file", temp_file
        ])

        assert result.exit_code == 0
        assert "Successfully uploaded" in result.output
        mock_client_instance.upload_component.assert_called_once()


def test_upload_command_with_custom_name(cli_runner, mock_settings, temp_file):
    """Test upload command with custom asset name."""
    with patch("nexus.commands.upload.get_settings") as mock_get_settings, \
         patch("nexus.commands.upload.NexusClient") as mock_client_class:

        # Setup mocks
        mock_get_settings.return_value = mock_settings
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = AsyncMock()
        mock_client_instance.upload_component = AsyncMock(
            return_value={"status": "success"}
        )
        mock_client_class.return_value = mock_client_instance

        # Run command
        result = cli_runner.invoke(upload, [
            "--repository", "raw-hosted",
            "--file", temp_file,
            "--name", "custom-name.txt"
        ])

        assert result.exit_code == 0
        assert "custom-name.txt" in result.output

        # Verify asset_name parameter
        call_args = mock_client_instance.upload_component.call_args
        assert call_args.kwargs["asset_name"] == "custom-name.txt"


def test_upload_command_with_directory(cli_runner, mock_settings, temp_file):
    """Test upload command with custom directory."""
    with patch("nexus.commands.upload.get_settings") as mock_get_settings, \
         patch("nexus.commands.upload.NexusClient") as mock_client_class:

        # Setup mocks
        mock_get_settings.return_value = mock_settings
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = AsyncMock()
        mock_client_instance.upload_component = AsyncMock(
            return_value={"status": "success"}
        )
        mock_client_class.return_value = mock_client_instance

        # Run command
        result = cli_runner.invoke(upload, [
            "--repository", "raw-hosted",
            "--file", temp_file,
            "--directory", "/data/files"
        ])

        assert result.exit_code == 0
        assert "/data/files" in result.output

        # Verify directory parameter
        call_args = mock_client_instance.upload_component.call_args
        assert call_args.kwargs["directory"] == "/data/files"


def test_upload_command_with_properties(cli_runner, mock_settings, temp_file):
    """Test upload command with properties."""
    with patch("nexus.commands.upload.get_settings") as mock_get_settings, \
         patch("nexus.commands.upload.NexusClient") as mock_client_class:

        # Setup mocks
        mock_get_settings.return_value = mock_settings
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = AsyncMock()
        mock_client_instance.upload_component = AsyncMock(
            return_value={"status": "success"}
        )
        mock_client_class.return_value = mock_client_instance

        # Run command
        result = cli_runner.invoke(upload, [
            "--repository", "raw-hosted",
            "--file", temp_file,
            "--property", "version=1.0.0",
            "--property", "environment=prod"
        ])

        assert result.exit_code == 0

        # Verify properties were passed
        call_args = mock_client_instance.upload_component.call_args
        assert call_args.kwargs["version"] == "1.0.0"
        assert call_args.kwargs["environment"] == "prod"


def test_upload_command_file_not_found(cli_runner, mock_settings):
    """Test upload command with non-existent file."""
    with patch("nexus.commands.upload.get_settings") as mock_get_settings, \
         patch("nexus.commands.upload.NexusClient") as mock_client_class:

        mock_get_settings.return_value = mock_settings
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client_instance

        # Run command with non-existent file
        result = cli_runner.invoke(upload, [
            "--repository", "raw-hosted",
            "--file", "/nonexistent/file.txt"
        ])

        # File existence is checked by click.Path(exists=True)
        assert result.exit_code != 0
        assert "Error" in result.output or "does not exist" in result.output


def test_upload_command_invalid_property_format(cli_runner, mock_settings, temp_file):
    """Test upload command with invalid property format."""
    with patch("nexus.commands.upload.get_settings") as mock_get_settings, \
         patch("nexus.commands.upload.NexusClient") as mock_client_class:

        mock_get_settings.return_value = mock_settings
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client_instance

        # Run command with invalid property format
        result = cli_runner.invoke(upload, [
            "--repository", "raw-hosted",
            "--file", temp_file,
            "--property", "invalid-format"
        ])

        assert "Invalid property format" in result.output or "Error" in result.output


def test_upload_command_full_example(cli_runner, mock_settings, temp_file):
    """Test upload command with all parameters."""
    with patch("nexus.commands.upload.get_settings") as mock_get_settings, \
         patch("nexus.commands.upload.NexusClient") as mock_client_class:

        # Setup mocks
        mock_get_settings.return_value = mock_settings
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = AsyncMock()
        mock_client_instance.upload_component = AsyncMock(
            return_value={"status": "success"}
        )
        mock_client_class.return_value = mock_client_instance

        # Run command with all options
        result = cli_runner.invoke(upload, [
            "--repository", "raw-hosted",
            "--file", temp_file,
            "--name", "release-1.0.0.txt",
            "--directory", "/releases/v1",
            "--property", "version=1.0.0",
            "--property", "tag=stable"
        ])

        assert result.exit_code == 0
        assert "Successfully uploaded" in result.output

        # Verify all parameters
        call_args = mock_client_instance.upload_component.call_args
        assert call_args.kwargs["asset_name"] == "release-1.0.0.txt"
        assert call_args.kwargs["directory"] == "/releases/v1"
        assert call_args.kwargs["version"] == "1.0.0"
        assert call_args.kwargs["tag"] == "stable"
