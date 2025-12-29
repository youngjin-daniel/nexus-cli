"""Tests for list command."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest
from click.testing import CliRunner

from nexus_cli.commands.list import list_assets


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
        },
        {
            "repository": "my-repo",
            "path": "MyProject/build_20250101_120000/component-b/artifact.zip",
            "downloadUrl": "https://nexus.example.com/test2",
        },
    ]


def test_list_command_no_tmp_dir(cli_runner):
    """Test list command when tmp directory doesn't exist."""
    with patch("pathlib.Path.exists", return_value=False):
        result = cli_runner.invoke(list_assets, [])
        
        assert result.exit_code == 1
        assert "Error: tmp directory does not exist" in result.output


def test_list_command_no_files(cli_runner):
    """Test list command when no search result files exist."""
    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.glob", return_value=[]):
        
        result = cli_runner.invoke(list_assets, [])
        
        assert result.exit_code == 1
        assert "Error: No search result files found" in result.output


def test_list_command_success_today(cli_runner, sample_search_results):
    """Test list command with today's search results."""
    today = datetime.now().strftime("%Y%m%d%H%M%S")
    test_file = f"search_{today}.json"
    
    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.glob", return_value=[Path(f"tmp/{test_file}")]), \
         patch("builtins.open", mock_open(read_data=json.dumps(sample_search_results))):
        
        result = cli_runner.invoke(list_assets, [])
        
        assert result.exit_code == 0
        assert "my-repo:" in result.output
        assert "artifact.zip" in result.output
        assert "Total: 2 item(s)" in result.output
        assert "STALED" not in result.output


def test_list_command_stale_warning(cli_runner, sample_search_results):
    """Test list command with stale search results."""
    old_date = "20251201120000"
    test_file = f"search_{old_date}.json"
    
    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.glob", return_value=[Path(f"tmp/{test_file}")]), \
         patch("builtins.open", mock_open(read_data=json.dumps(sample_search_results))):
        
        result = cli_runner.invoke(list_assets, [])
        
        assert result.exit_code == 0
        assert "WARNING: Search results are stale (STALED)" in result.output


def test_list_command_empty_results(cli_runner):
    """Test list command with empty search results."""
    today = datetime.now().strftime("%Y%m%d%H%M%S")
    test_file = f"search_{today}.json"
    
    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.glob", return_value=[Path(f"tmp/{test_file}")]), \
         patch("builtins.open", mock_open(read_data="[]")):
        
        result = cli_runner.invoke(list_assets, [])
        
        assert result.exit_code == 0
        assert "Total: 0 item(s)" in result.output
