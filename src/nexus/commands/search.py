"""Search command implementation."""

import asyncio

import click

from nexus.client import NexusClient
from nexus.config import get_settings


@click.command()
@click.option("--repository", "-r", default=None, help="Repository name to search in (default: from NEXUS_REPOSITORY env or 'my-repo')")
@click.option("--pattern", "-p", multiple=True, required=True, help="Name pattern to search (supports wildcards, can be used multiple times)")
@click.option("--debug", is_flag=True, help="Show debug information")
@click.pass_context
def search(ctx, repository: str, pattern: tuple, debug: bool):
    """Search Nexus repository assets using web UI style.

    Search using Name patterns just like the web UI.

    Examples:
        # Single pattern search
        nexus search -p "MyProject/build_20250101*artifact.zip"

        # Multiple pattern search
        nexus search -p "MyProject/build_20250101*artifact.zip" -p "MyProject/build_20250101*.tar.gz"
    """
    asyncio.run(_search_async(ctx, repository, pattern, debug))


async def _search_async(ctx, repository: str, patterns: tuple, debug: bool):
    """Async implementation of search command."""
    # Get settings from context or create new
    settings = ctx.obj if ctx.obj else get_settings()

    # Use repository from settings if not provided
    if not repository:
        repository = settings.repository

    return await perform_search(settings, repository, patterns, debug)


async def perform_search(settings, repository: str, patterns: tuple, debug: bool):
    """Perform search and return results. Can be called from other commands."""
    async with NexusClient(
        base_url=settings.host,
        username=settings.username,
        password=settings.password,
        timeout=settings.timeout,
        verify_ssl=settings.verify_ssl,
    ) as client:
        all_assets = []

        # Search for each pattern
        for pattern in patterns:
            click.echo(f"Searching: {pattern}", err=True)

            search_params = {
                "repository": repository,
                "name": pattern
            }

            if debug:
                click.echo(f"[DEBUG] API parameters: {search_params}", err=True)

            async for asset in client.search_assets(**search_params):
                path = asset.get("path", "N/A")
                click.echo(f"  - {path}", err=True)
                all_assets.append(asset)

            click.echo("", err=True)

        return all_assets
