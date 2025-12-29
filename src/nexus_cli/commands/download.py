"""Download command implementation."""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import click

from nexus_cli.client import NexusClient
from nexus_cli.config import get_settings


@click.command()
@click.option("--output-dir", "-o", default=".", help="Output directory for downloaded files (default: current directory)")
@click.option("--force-search", is_flag=True, help="Force search before download")
@click.option("--pattern", "-p", multiple=True, help="Search pattern (required with --force-search)")
@click.option("--repository", "-r", default=None, help="Repository name (default: from NEXUS_REPOSITORY env or 'my-repo', used with --force-search)")
@click.pass_context
def download(ctx, output_dir: str, force_search: bool, pattern: tuple, repository: str):
    """Download all assets based on the latest search JSON file.

    Reads the latest search_*.json file and downloads all assets.
    Each file is saved using the last two path components.

    Examples:
        # Download based on latest JSON file
        nexus download

        # Download to specific path
        nexus download -o /path/to/save

        # Force search before download
        nexus download --force-search -p "MyProject/build_20250101*artifact.zip"
    """
    asyncio.run(_download_async(ctx, output_dir, force_search, pattern, repository))


async def _download_async(ctx, output_dir: str, force_search: bool, patterns: tuple, repository: str):
    """Async implementation of download command."""
    settings = ctx.obj if ctx.obj else get_settings()
    
    # Use repository from settings if not provided
    if not repository:
        repository = settings.repository
    
    try:
        # If force search is enabled
        if force_search:
            if not patterns:
                click.echo("Error: --pattern is required with --force-search", err=True)
                ctx.exit(1)
            
            click.echo("Running forced search...", err=True)
            
            # Run search
            from nexus_cli.commands.search import _search_async as search_async
            
            # Create temporary context (to call search_async)
            temp_ctx = click.Context(click.Command('search'))
            temp_ctx.obj = settings
            
            await search_async(temp_ctx, repository, patterns, False)
            click.echo("", err=True)
        
        # Find latest JSON file
        tmp_dir = Path("tmp")
        if not tmp_dir.exists():
            click.echo("Error: tmp directory does not exist.", err=True)
            click.echo("Please run 'nexus search' command first.", err=True)
            ctx.exit(1)
        
        search_files = list(tmp_dir.glob("search_*.json"))
        if not search_files:
            click.echo("Error: No search result files found.", err=True)
            click.echo("Please run 'nexus search' command first.", err=True)
            ctx.exit(1)
        
        latest_file = sorted(search_files)[-1]
        click.echo(f"Using JSON file: {latest_file}", err=True)
        
        # Read JSON file
        with open(latest_file, "r", encoding="utf-8") as f:
            assets = json.load(f)
        
        if not assets:
            click.echo("Error: JSON file is empty.", err=True)
            ctx.exit(1)
        
        click.echo(f"Files to download: {len(assets)}", err=True)
        click.echo("", err=True)
        
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_path = Path(output_dir) / f"artifacts_{timestamp}"
        output_path.mkdir(parents=True, exist_ok=True)
        
        click.echo(f"Download path: {output_path}", err=True)
        click.echo("", err=True)
        
        # Create Nexus client
        async with NexusClient(
            base_url=settings.host,
            username=settings.username,
            password=settings.password,
            timeout=settings.timeout,
            verify_ssl=settings.verify_ssl,
        ) as client:
            # Download each asset
            success_count = 0
            fail_count = 0
            
            for i, asset in enumerate(assets, 1):
                path = asset.get("path", "")
                download_url = asset.get("downloadUrl", "")
                
                if not download_url:
                    click.echo(f"[{i}/{len(assets)}] ⚠️  Skip: {path} (no downloadUrl)", err=True)
                    fail_count += 1
                    continue
                
                # Extract last two path components
                # Example: MyProject/build_20250101_120000/component-a/file.tar.gz
                # → component-a/file.tar.gz
                path_parts = path.split("/")
                if len(path_parts) >= 2:
                    relative_path = "/".join(path_parts[-2:])
                else:
                    relative_path = path_parts[-1] if path_parts else "unknown"
                
                dest_file = output_path / relative_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    click.echo(f"[{i}/{len(assets)}] Downloading: {relative_path}", err=True)
                    
                    # Download file
                    await client.download_asset(download_url, dest_file)
                    
                    success_count += 1
                    click.echo(f"[{i}/{len(assets)}] ✅ Completed: {dest_file}", err=True)
                    
                except Exception as e:
                    fail_count += 1
                    click.echo(f"[{i}/{len(assets)}] ❌ Failed: {relative_path} - {e}", err=True)
        
        # Print results
        click.echo("", err=True)
        click.echo("=" * 60, err=True)
        click.echo("Download completed!", err=True)
        click.echo(f"  Success: {success_count} file(s)", err=True)
        click.echo(f"  Failed: {fail_count} file(s)", err=True)
        click.echo(f"  Saved to: {output_path}", err=True)
        click.echo("=" * 60, err=True)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        import traceback
        click.echo(traceback.format_exc(), err=True)
        ctx.exit(1)
