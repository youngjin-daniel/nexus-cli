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

- Python 3.11 or higher
- uv (recommended package manager)

### Development Mode Installation

```bash
# Create virtual environment and install dependencies
uv sync --dev

# Run CLI
uv run nexus --help
```

### Production Installation

```bash
# Install using uv
uv pip install .

# Or install using pip
pip install .
```

## Configuration

Configuration is loaded in the following priority order:

1. CLI options (highest priority)
2. Environment variables
3. Default values

### Environment Variables

```bash
export NEXUS_HOST=https://nexus.example.com
export NEXUS_REPOSITORY=my-repo      # Optional (default: my-repo)
export NEXUS_USER=username           # Optional
export NEXUS_PASS=password           # Optional
export NEXUS_TIMEOUT=30              # Optional (default: 30)
export NEXUS_VERIFY_SSL=true         # Optional (default: true)
```

## Usage

### Workflow: Search → List → Download

This CLI follows a three-step workflow for efficient asset management:

#### 1. Search

Search for assets using web UI style patterns with wildcards:

```bash
# Search for artifact files in daily builds
nexus search -r my-repo -p "MyProject/build_20250101*artifact.zip"

# Search with multiple patterns
nexus search -r my-repo \
    -p "MyProject/build_20250101*artifact.zip" \
    -p "MyProject/build_20250101*.tar.gz"

# Debug mode for detailed output
nexus search -r my-repo -p "MyProject/*artifact.zip" --debug
```

Results are saved to `tmp/search_<timestamp>.json`.

#### 2. List

Display the latest search results:

```bash
# Show latest search results
nexus list

# Example output:
# my-repo: MyProject/build_20250101_120000/component-a/artifact.zip
# my-repo: MyProject/build_20250101_120000/component-b/artifact.zip
# Total: 2 item(s)
```

If search results are not from today, a STALED warning will be shown.

#### 3. Download

Download all assets from the latest search results:

```bash
# Download based on latest search results
nexus download

# Download to specific directory
nexus download -o /path/to/save

# Force search before download
nexus download --force-search \
    -p "MyProject/build_20250101*artifact.zip" \
    -r my-repo
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

Available for all commands:

```bash
nexus --host https://custom-nexus.com \
      --username myuser \
      --password mypass \
      --timeout 60 \
      --no-verify-ssl \
      search -r my-repo -p "pattern*"
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
│       │   ├── search.py        # Search command
│       │   └── list.py          # List command
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py      # Configuration loader
│       └── utils/
│           └── __init__.py
├── tmp/                         # Search result cache
│   └── search_*.json            # Saved search results
├── tests/
│   ├── conftest.py
│   ├── test_search.py
│   ├── test_download.py
│   ├── test_list.py
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
  - Results saved to `tmp/search_<timestamp>.json`
- `list.py`: Display latest search results
  - Automatic stale detection
  - Simple `repository: path` format
- `download.py`: Batch download from JSON
  - Downloads all assets from latest search results
  - Path extraction (last two components)
  - `--force-search` option for search + download
- `upload.py`: Upload with metadata and properties

### Configuration

Configuration priority:

1. CLI options (`--host`, `--username`, etc.)
2. Environment variables (`NEXUS_HOST`, `NEXUS_USER`, etc.)
3. Default values

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
