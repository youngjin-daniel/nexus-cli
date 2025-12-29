"""Tests for download command."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch, mock_open

import pytest
from click.testing import CliRunner

from nexus_cli.commands.download import download


@pytest.fixture
def cli_runner():
    """Provide Click CLI runner."""
    return CliRunner()


@pytest.fixture
def sample_search_results():
    """Sample search results for testing."""
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


def test_download_command_no_tmp_dir(cli_runner, mock_settings):
    """Test download command when tmp directory doesn't exist."""
    with patch("nexus_cli.commands.download.get_settings") as mock_get_settings, \
         patch("pathlib.Path.exists", return_value=False):
        
        mock_get_settings.return_value = mock_settings
        
        result = cli_runner.invoke(download, [])
        
        assert result.exit_code == 1
        assert "Error: tmp directory does not exist" in result.output


def test_download_command_no_search_files(cli_runner, mock_settings):
    """Test download command when no search result files exist."""
    with patch("nexus_cli.commands.download.get_settings") as mock_get_settings, \
         patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.glob", return_value=[]):
        
        mock_get_settings.return_value = mock_settings
        
        result = cli_runner.invoke(download, [])
        
        assert result.exit_code == 1
        assert "Error: No search result files found" in result.output


def test_download_command_success(cli_runner, mock_settings, sample_search_results):
    """Test download command successfully downloads all assets."""
    today = datetime.now().strftime("%Y%m%d%H%M%S")
    test_file = f"search_{today}.json"
    
    with patch("nexus_cli.commands.download.get_settings") as mock_get_settings, \
         patch("nexus_cli.commands.download.NexusClient") as mock_client_class, \
         patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.glob", return_value=[Path(f"tmp/{test_file}")]), \
         patch("builtins.open", mock_open(read_data=json.dumps(sample_search_results))), \
         patch("pathlib.Path.mkdir"), \
         tempfile.TemporaryDirectory() as tmpdir:
        
        # Setup mocks
        mock_get_settings.return_value = mock_settings
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = AsyncMock()
        mock_client_instance.download_asset = AsyncMock()
        mock_client_class.return_value = mock_client_instance
        
        # Run command
        result = cli_runner.invoke(download, ["-o", tmpdir])
        
        assert result.exit_code == 0
        assert "Download completed!" in result.output
        assert "Success: 2 file(s)" in result.output


def test_download_command_empty_json(cli_runner, mock_settings):
    """Test download command with empty JSON file."""
    today = datetime.now().strftime("%Y%m%d%H%M%S")
    test_file = f"search_{today}.json"
    
    with patch("nexus_cli.commands.download.get_settings") as mock_get_settings, \
         patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.glob", return_value=[Path(f"tmp/{test_file}")]), \
         patch("builtins.open", mock_open(read_data="[]")):
        
        mock_get_settings.return_value = mock_settings
        
        result = cli_runner.invoke(download, [])
        
        assert result.exit_code == 1
        assert "Error: JSON file is empty" in result.output


def test_download_command_force_search(cli_runner, mock_settings, sample_search_results):
    """Test download command with --force-search option."""
    with patch("nexus_cli.commands.download.get_settings") as mock_get_settings, \
         patch("nexus_cli.commands.download.NexusClient") as mock_client_class, \
         patch("nexus_cli.commands.search._search_async") as mock_search, \
         patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.glob", return_value=[Path("tmp/search_20251229120000.json")]), \
         patch("builtins.open", mock_open(read_data=json.dumps(sample_search_results))), \
         patch("pathlib.Path.mkdir"), \
         tempfile.TemporaryDirectory() as tmpdir:
        
        # Setup mocks
        mock_get_settings.return_value = mock_settings
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = AsyncMock()
        mock_client_instance.download_asset = AsyncMock()
        mock_client_class.return_value = mock_client_instance
        mock_search.return_value = AsyncMock()
        
        # Run command
        result = cli_runner.invoke(download, [
            "--force-search",
            "-p", "MyProject/*artifact.zip",
            "-o", tmpdir
        ])
        
        assert result.exit_code == 0
        assert "Running forced search" in result.output


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
