# Nexus CLI

Python-based CLI tool for Nexus Repository OSS. Provides file search, download, and upload functionality.

## Features

- **Search**: Web UI style asset search with wildcard patterns
- **List**: Display latest search results with stale detection
- **Download**: Batch download based on search results (streaming support)
- **Upload**: File upload with metadata and properties
- **Cross-platform**: Ubuntu and macOS support
- **Async I/O**: Efficient network processing using httpx

## Installation

### Requirements

- Python 3.11 or higher (for development and pip installation)
- uv (recommended package manager for development)

### Option 1: Binary Installation (Recommended for End Users)

Download or build a standalone binary that works without Python installation:

#### Build Binary

```bash
# Install PyInstaller
uv add --dev pyinstaller

# Build standalone binary
uv run pyinstaller --onefile --name nexus --clean src/nexus_cli/__main__.py

# Binary will be created at dist/nexus
```

#### Install Binary Globally

**macOS/Linux**:
```bash
# Install to /usr/local/bin (requires sudo)
sudo cp dist/nexus /usr/local/bin/
sudo chmod +x /usr/local/bin/nexus

# Or install to user bin (no sudo required)
mkdir -p ~/.local/bin
cp dist/nexus ~/.local/bin/
chmod +x ~/.local/bin/nexus

# Make sure ~/.local/bin is in your PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc  # or ~/.bashrc
source ~/.zshrc
```

**Verify installation**:
```bash
nexus --version
nexus --help
```

### Option 2: Development Mode Installation

```bash
# Create virtual environment and install dependencies
uv sync --dev

# Run CLI
uv run nexus --help
```

### Option 3: Python Package Installation

```bash
# Install using uv
uv pip install .

# Or install using pip
pip install .
```

## Building and Publishing

### Build Standalone Binary

For end users who don't have Python installed:

```bash
# Build standalone executable
uv run pyinstaller --onefile --name nexus --clean src/nexus_cli/__main__.py

# Output: dist/nexus (macOS/Linux) or dist/nexus.exe (Windows)
# File size: ~12MB (includes Python runtime and all dependencies)
```

### Build Python Package

For distribution via PyPI:

```bash
# Build wheel and source distribution
uv build

# Or using python -m build
python -m build
```

This creates distribution files in the `dist/` directory:
- `nexus_cli-0.1.0-py3-none-any.whl` (wheel package)
- `nexus_cli-0.1.0.tar.gz` (source distribution)

### Install from Built Package

```bash
# Install from wheel
uv pip install dist/nexus_cli-0.1.0-py3-none-any.whl

# Or using pip
pip install dist/nexus_cli-0.1.0-py3-none-any.whl
```

After installation, the `nexus` command will be available globally:

```bash
nexus --help
nexus search -r my-repo -p "MyProject/*artifact.zip"
```

### Publish to PyPI

```bash
# Install twine if not already installed
uv pip install twine

# Upload to PyPI (requires PyPI account and API token)
twine upload dist/*

# Or upload to Test PyPI first
twine upload --repository testpypi dist/*
```

After publishing, users can install with:

```bash
pip install nexus-cli
```

## Configuration

Configuration is loaded in the following priority order:

1. CLI options (highest priority)
2. Environment variables

**Required settings**: `NEXUS_HOST` and `NEXUS_REPOSITORY` must be provided via CLI options or environment variables.

### Environment Variables

```bash
# Required
export NEXUS_HOST=https://nexus.example.com
export NEXUS_REPOSITORY=my-repo

# Optional
export NEXUS_USER=username           # For authenticated repositories
export NEXUS_PASS=password           # For authenticated repositories
export NEXUS_TIMEOUT=30              # Request timeout in seconds (default: 30)
export NEXUS_VERIFY_SSL=true         # SSL verification (default: true)
```

## Usage

### Search and Download Workflow

This CLI provides two main commands for asset management:

#### Search

Search for assets using web UI style patterns with wildcards. Results are displayed directly:

```bash
# Search for artifact files (assuming environment variables are set)
nexus search -p "MyProject/build_20250101*artifact.zip"

# Or with explicit options
nexus --host https://nexus.example.com -r my-repo \
    search -p "MyProject/build_20250101*artifact.zip"

# Example output:
# Searching: MyProject/build_20250101*artifact.zip
#   - MyProject/build_20250101_120000/component-a/artifact.zip
#   - MyProject/build_20250101_120000/component-b/artifact.zip

# Search with multiple patterns
nexus search \
    -p "MyProject/build_20250101*artifact.zip" \
    -p "MyProject/build_20250101*.tar.gz"

# Debug mode for detailed output
nexus search -p "MyProject/*artifact.zip" --debug
```

#### Download

Search and download matching assets in one command:

```bash
# Search and download (assuming environment variables are set)
nexus download -p "MyProject/build_20250101*artifact.zip"

# Or with explicit options
nexus --host https://nexus.example.com -r my-repo \
    download -p "MyProject/build_20250101*artifact.zip"

# Download to specific directory
nexus download -p "MyProject/build_20250101*artifact.zip" -o /path/to/save

# Multiple patterns
nexus download \
    -p "MyProject/build_20250101*artifact.zip" \
    -p "MyProject/build_20250101*.tar.gz"
```

Files are saved to `artifacts_<timestamp>/` directory using the last two path components.

Example:

- Path: `MyProject/build_20250101_120000/component-a/file.tar.gz`
- Saved to: `artifacts_20250101_140000/component-a/file.tar.gz`

### Upload (Not tested yet)

```bash
# Upload file
nexus upload --repository raw-hosted --file ./myfile.txt

# Upload with custom name and directory
nexus upload --repository raw-hosted --file ./myfile.txt \
    --name custom-name.txt --directory /data/files

# Upload with properties
nexus upload --repository raw-hosted --file ./myfile.txt \
    --property version=1.0.0 --property environment=prod
```

### Global Options

Available for all commands (required options must be provided):

```bash
# All options
nexus --host https://nexus.example.com \
      --repository my-repo \
      --username myuser \
      --password mypass \
      --timeout 60 \
      --no-verify-ssl \
      search -p "pattern*"

# Minimum required options (if not set via environment variables)
nexus --host https://nexus.example.com -r my-repo search -p "pattern*"
```

## Development

### Project Structure

```
nexus_cli/
├── src/
│   └── nexus_cli/
│       ├── __init__.py
│       ├── __main__.py          # CLI entry point
│       ├── cli.py               # Click CLI definition
│       ├── client/
│       │   ├── __init__.py
│       │   └── nexus_client.py  # NexusClient class
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── upload.py        # Upload command
│       │   ├── download.py      # Download command
│       │   └── search.py        # Search command
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py      # Configuration loader
│       └── utils/
│           └── __init__.py
├── tests/
│   ├── conftest.py
│   ├── test_search.py
│   ├── test_download.py
│   └── test_upload.py
├── pyproject.toml
└── README.md
```

### Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=nexus_cli --cov-report=html

# Run specific test
uv run pytest tests/test_search.py -v
```

### Lint and Format

```bash
# Check code
uv run ruff check src/

# Format code
uv run ruff format src/
```

## Architecture

### NexusClient

Async HTTP client for Nexus REST API v1:

- `list_repositories()`: List repositories
- `search_components(**params)`: Search components (with pagination)
- `search_assets(**params)`: Search assets (with pagination)
- `download_asset(url, dest)`: Streaming download
- `upload_component(repo, file, **metadata)`: Streaming upload

### Command Layer

Each command is implemented as an independent module:

- `search.py`: Web UI style search with wildcard patterns
  - Server-side filtering using `name` parameter
  - Outputs matching paths to stderr
  - Provides `perform_search()` function for reuse
- `download.py`: Search and download in one command
  - Performs search using patterns
  - Downloads all matching assets
  - Path extraction (last two components)
- `upload.py`: Upload with metadata and properties

### Configuration

Configuration priority:

1. CLI options (`--host`, `--repository`, etc.) - highest priority
2. Environment variables (`NEXUS_HOST`, `NEXUS_REPOSITORY`, etc.)

**Required**: `NEXUS_HOST` and `NEXUS_REPOSITORY` must be provided via one of the above methods.

## API Reference

This tool uses Nexus Repository Manager REST API v1:

- [Nexus REST APIs Documentation](https://help.sonatype.com/en/rest-apis-307236.html)
- Components API: `/service/rest/v1/components`
- Search API: `/service/rest/v1/search`
- Assets API: `/service/rest/v1/assets`

## Key Implementation Details

### Search Strategy

Unlike traditional keyword-based search, this tool uses the **Name parameter with wildcards** for server-side filtering, matching the Nexus web UI behavior:

- **Fast**: Server-side filtering (700x faster than client-side)
- **Efficient**: Only matching assets are returned
- **Flexible**: Support for wildcard patterns (`*`, `?`)

Example:

```bash
# Web UI equivalent: Name field = "MyProject/build_20250101*artifact.zip"
nexus search -r my-repo -p "MyProject/build_20250101*artifact.zip"
```

### Path Extraction

Download command extracts the last two path components for clean folder structure:

```
Original: MyProject/build_20250101_120000/component-a/component-b/artifact.zip
Saved as: artifacts_20250101_140000/component-b/artifact.zip
```

This prevents deep nested directories and makes downloaded files easier to manage.

## License

MIT License
