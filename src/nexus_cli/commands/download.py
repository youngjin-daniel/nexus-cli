"""Download command implementation."""

import asyncio
from datetime import datetime
from pathlib import Path

import click

from nexus_cli.client import NexusClient
from nexus_cli.config import get_settings
from nexus_cli.commands.search import perform_search


@click.command()
@click.option("--output-dir", "-o", default=".", help="Output directory for downloaded files (default: current directory)")
@click.option("--pattern", "-p", multiple=True, required=True, help="Search pattern (supports wildcards, can be used multiple times)")
@click.option("--repository", "-r", default=None, help="Repository name (default: from NEXUS_REPOSITORY env or 'my-repo')")
@click.option("--debug", is_flag=True, help="Show debug information")
@click.pass_context
def download(ctx, output_dir: str, pattern: tuple, repository: str, debug: bool):
    """Search and download all matching assets.

    First searches for assets using the specified patterns, then downloads all matches.
    Each file is saved using the last two path components.

    Examples:
        # Search and download
        nexus download -p "MyProject/build_20250101*artifact.zip"

        # Download to specific path
        nexus download -o /path/to/save -p "MyProject/*artifact.zip"

        # Multiple patterns
        nexus download -p "MyProject/*artifact.zip" -p "MyProject/*.tar.gz"
    """
    asyncio.run(_download_async(ctx, output_dir, pattern, repository, debug))


async def _download_async(ctx, output_dir: str, patterns: tuple, repository: str, debug: bool):
    """Async implementation of download command."""
    settings = ctx.obj if ctx.obj else get_settings()

    # Use repository from settings if not provided
    if not repository:
        repository = settings.repository

    try:
        # Perform search first
        assets = await perform_search(settings, repository, patterns, debug)

        if not assets:
            click.echo("No assets found matching the patterns.", err=True)
            ctx.exit(1)

        click.echo(f"Found {len(assets)} asset(s). Starting download...", err=True)
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
