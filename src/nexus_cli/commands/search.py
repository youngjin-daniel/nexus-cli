"""Search command implementation."""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import click

from nexus_cli.client import NexusClient
from nexus_cli.config import get_settings


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

    async with NexusClient(
        base_url=settings.host,
        username=settings.username,
        password=settings.password,
        timeout=settings.timeout,
        verify_ssl=settings.verify_ssl,
    ) as client:
        try:
            # Search start time
            start_time = datetime.now()
            search_time = start_time.strftime("%Y%m%d%H%M%S")
            
            # JSON file save path
            tmp_dir = Path("tmp")
            tmp_dir.mkdir(exist_ok=True)
            json_file = tmp_dir / f"search_{search_time}.json"
            
            click.echo(f"Search started: {repository} repository", err=True)
            click.echo(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}", err=True)
            click.echo(f"Patterns: {len(patterns)} pattern(s)", err=True)
            click.echo(f"Results will be saved to: {json_file}", err=True)
            click.echo("", err=True)
            
            # All assets list
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
                
                count = 0
                async for asset in client.search_assets(**search_params):
                    count += 1
                    
                    if debug and count <= 3:
                        click.echo(f"[DEBUG] Asset: {asset.get('path', 'N/A')}", err=True)
                    
                    all_assets.append(asset)
                
                click.echo(f"  → {count} asset(s) found", err=True)
            
            # Save to JSON file
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(all_assets, f, indent=2, ensure_ascii=False)
            
            # End time
            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            
            click.echo("", err=True)
            click.echo("✅ Search completed!", err=True)
            click.echo(f"   - Total assets: {len(all_assets)}", err=True)
            click.echo(f"   - Results file: {json_file}", err=True)
            click.echo(f"   - Completion time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}", err=True)
            click.echo(f"   - Elapsed time: {elapsed:.1f}s ({elapsed/60:.1f}min)", err=True)
            
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            if debug:
                import traceback
                click.echo(traceback.format_exc(), err=True)
            ctx.exit(1)
