"""List command implementation."""

import json
from datetime import datetime
from pathlib import Path

import click


@click.command(name="list")
def list_assets():
    """Display the latest search results.
    
    Automatically finds and displays the most recent search_*.json file
    in repository: path format.
    """
    try:
        # Find search_*.json files in tmp directory
        tmp_dir = Path("tmp")
        if not tmp_dir.exists():
            click.echo("Error: tmp directory does not exist.", err=True)
            click.echo("Please run 'nexus search' command first.", err=True)
            return
        
        # Find search_*.json pattern files
        search_files = list(tmp_dir.glob("search_*.json"))
        
        if not search_files:
            click.echo("Error: No search result files found.", err=True)
            click.echo("Please run 'nexus search' command first.", err=True)
            return
        
        # Sort by filename (contains timestamp, so string sort is sufficient)
        latest_file = sorted(search_files)[-1]
        
        # Extract date from filename (search_YYYYMMDDHHMMSS.json)
        file_name = latest_file.stem  # search_20251229193737
        file_date_str = file_name.replace("search_", "")[:8]  # 20251229
        
        # Today's date
        today_str = datetime.now().strftime("%Y%m%d")
        
        click.echo(f"File: {latest_file}", err=True)
        
        # Compare dates
        if file_date_str != today_str:
            click.echo("", err=True)
            click.echo("⚠️  WARNING: Search results are stale (STALED)", err=True)
            click.echo(f"   File date: {file_date_str}", err=True)
            click.echo(f"   Today's date: {today_str}", err=True)
            click.echo("   Run 'nexus search' command again to get fresh results.", err=True)
        
        click.echo("", err=True)
        
        # Read JSON file
        with open(latest_file, "r", encoding="utf-8") as f:
            assets = json.load(f)
        
        if not assets:
            click.echo("Search results are empty.", err=True)
            return
        
        # Print in repository: path format
        for asset in assets:
            repository = asset.get("repository", "N/A")
            path = asset.get("path", "N/A")
            click.echo(f"{repository}: {path}")
        
        click.echo("", err=True)
        click.echo(f"Total: {len(assets)} item(s)", err=True)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        import traceback
        click.echo(traceback.format_exc(), err=True)
