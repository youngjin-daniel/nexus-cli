"""Nexus Repository Manager API Client."""

from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional

import httpx


class NexusClient:
    """Async HTTP client for Nexus Repository Manager REST API."""

    def __init__(
        self,
        base_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30,
        verify_ssl: bool = True,
    ):
        """Initialize NexusClient.

        Args:
            base_url: Base URL of Nexus server (e.g., https://nexus.example.com)
            username: Optional username for authentication
            password: Optional password for authentication
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Configure authentication if provided
        auth = None
        if username and password:
            auth = (username, password)

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            auth=auth,
            timeout=timeout,
            verify=verify_ssl,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def list_repositories(self) -> list[Dict[str, Any]]:
        """List all repositories.

        Returns:
            List of repository information dictionaries
        """
        response = await self.client.get("/service/rest/v1/repositories")
        response.raise_for_status()
        return response.json()

    async def list_components(
        self, repository: str, **params
    ) -> AsyncIterator[Dict[str, Any]]:
        """List components in a repository with pagination.

        Args:
            repository: Repository name
            **params: Additional query parameters

        Yields:
            Component information dictionaries
        """
        params["repository"] = repository
        async for item in self._paginate("/service/rest/v1/components", params):
            yield item

    async def search_components(self, **params) -> AsyncIterator[Dict[str, Any]]:
        """Search for components with pagination.

        Args:
            **params: Search parameters (repository, name, group, version, etc.)

        Yields:
            Component information dictionaries
        """
        async for item in self._paginate("/service/rest/v1/search", params):
            yield item

    async def search_assets(self, **params) -> AsyncIterator[Dict[str, Any]]:
        """Search for assets with pagination.

        Args:
            **params: Search parameters (repository, name, sha1, etc.)

        Yields:
            Asset information dictionaries
        """
        async for item in self._paginate("/service/rest/v1/search/assets", params):
            yield item

    async def download_asset(
        self, download_url: str, dest_path: Path, chunk_size: int = 8192
    ) -> None:
        """Download an asset to a file with streaming.

        Args:
            download_url: Asset download URL (can be relative or absolute)
            dest_path: Destination file path
            chunk_size: Size of chunks to read/write in bytes
        """
        # Handle relative URLs
        if not download_url.startswith("http"):
            download_url = f"{self.base_url}{download_url}"

        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        async with self.client.stream("GET", download_url) as response:
            response.raise_for_status()
            with open(dest_path, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                    f.write(chunk)

    async def upload_component(
        self,
        repository: str,
        file_path: Path,
        asset_name: Optional[str] = None,
        **metadata,
    ) -> Dict[str, Any]:
        """Upload a component to a repository.

        Args:
            repository: Repository name
            file_path: Path to the file to upload
            asset_name: Optional custom name for the asset (defaults to filename)
            **metadata: Additional metadata (tags, properties, etc.)

        Returns:
            Upload response data
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if asset_name is None:
            asset_name = file_path.name

        # Prepare multipart form data
        files = {"raw.asset1": (asset_name, open(file_path, "rb"))}
        data = {
            "raw.directory": metadata.get("directory", "/"),
            "raw.asset1.filename": asset_name,
        }

        # Add any additional metadata
        for key, value in metadata.items():
            if key not in ("directory",):
                data[key] = value

        url = f"/service/rest/v1/components?repository={repository}"

        try:
            response = await self.client.post(url, files=files, data=data)
            response.raise_for_status()
            return response.json() if response.text else {"status": "success"}
        finally:
            # Close file handles
            for _, file_tuple in files.items():
                if hasattr(file_tuple[1], "close"):
                    file_tuple[1].close()

    async def list_directory(
        self, repository: str, path: str = "", debug: bool = False
    ) -> list[Dict[str, Any]]:
        """List contents of a directory in the repository.

        This uses the repository browsing endpoint which is more efficient
        than searching all assets.

        Args:
            repository: Repository name
            path: Directory path (relative to repository root)
            debug: Enable debug output

        Returns:
            List of directory entries
        """
        # Normalize path
        path = path.strip("/")
        if path:
            # Try without trailing slash first
            url = f"/repository/{repository}/{path}"
        else:
            url = f"/repository/{repository}/"

        if debug:
            print(f"[DEBUG] Requesting URL: {self.base_url}{url}")

        try:
            response = await self.client.get(url, follow_redirects=True)

            if debug:
                print(f"[DEBUG] Response status: {response.status_code}")
                print(f"[DEBUG] Content-Type: {response.headers.get('content-type')}")
                print(f"[DEBUG] Response length: {len(response.text)} bytes")
                if response.status_code == 200:
                    print(f"[DEBUG] First 500 chars: {response.text[:500]}")

            response.raise_for_status()

            # Check if we got HTML (directory listing) or JSON
            content_type = response.headers.get("content-type", "")

            if "application/json" in content_type:
                return response.json()
            elif "text/html" in content_type:
                # Parse HTML directory listing
                entries = self._parse_directory_html(response.text, repository, path)
                if debug:
                    print(f"[DEBUG] Parsed {len(entries)} entries from HTML")
                return entries
            else:
                # Unknown response type
                if debug:
                    print(f"[DEBUG] Unknown content type: {content_type}")
                return []

        except httpx.HTTPStatusError as e:
            if debug:
                print(f"[DEBUG] HTTP Error: {e.response.status_code}")
            if e.response.status_code == 404:
                return []
            raise

    def _parse_directory_html(
        self, html: str, repository: str, base_path: str
    ) -> list[Dict[str, Any]]:
        """Parse HTML directory listing.

        Args:
            html: HTML content
            repository: Repository name
            base_path: Base path being listed

        Returns:
            List of directory entries with name and type
        """
        import re

        entries = []
        # Look for links in the HTML
        # Nexus uses <a href="...">...</a> for directory entries
        link_pattern = r'<a href="([^"]+)">([^<]+)</a>'

        for match in re.finditer(link_pattern, html):
            href, text = match.groups()

            # Skip parent directory link
            if href == "../":
                continue

            # Determine if it's a directory (ends with /)
            is_directory = href.endswith("/")
            name = href.rstrip("/")

            if name and not name.startswith("?"):  # Skip query links
                entry = {
                    "name": name,
                    "path": f"{base_path}/{name}".lstrip("/") if base_path else name,
                    "type": "directory" if is_directory else "file",
                    "repository": repository,
                }
                entries.append(entry)

        return entries

    async def _paginate(
        self, endpoint: str, params: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """Internal method to handle paginated API responses.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Yields:
            Items from paginated responses
        """
        continuation_token = None
        current_params = params.copy()

        while True:
            if continuation_token:
                current_params["continuationToken"] = continuation_token

            response = await self.client.get(endpoint, params=current_params)
            response.raise_for_status()
            data = response.json()

            # Yield all items in current page
            items = data.get("items", [])
            for item in items:
                yield item

            # Check for next page
            continuation_token = data.get("continuationToken")
            if not continuation_token:
                break
