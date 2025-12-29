"""Upload command implementation."""

import asyncio
from pathlib import Path
from typing import Optional

import click

from nexus_cli.client import NexusClient
from nexus_cli.config import get_settings


@click.command()
@click.option("--repository", "-r", required=True, help="Repository name")
@click.option(
    "--file", "-f", "file_path", type=click.Path(exists=True), required=True, help="File to upload"
)
@click.option("--name", "-n", help="Custom asset name (defaults to filename)")
@click.option(
    "--directory", "-d", default="/", help="Directory path in repository (default: /)"
)
@click.option(
    "--property",
    "-p",
    multiple=True,
    help="Property in key=value format (can be specified multiple times)",
)
@click.pass_context
def upload(
    ctx,
    repository: str,
    file_path: str,
    name: Optional[str],
    directory: str,
    property: tuple,
):
    """Upload a file to Nexus repository.

    Examples:

        # Upload file to root directory
        nexus upload --repository raw-hosted --file ./myfile.txt

        # Upload with custom name and directory
        nexus upload --repository raw-hosted --file ./myfile.txt \\
            --name custom-name.txt --directory /data/files

        # Upload with properties
        nexus upload --repository raw-hosted --file ./myfile.txt \\
            --property version=1.0.0 --property environment=prod
    """
    asyncio.run(_upload_async(ctx, repository, file_path, name, directory, property))


async def _upload_async(
    ctx,
    repository: str,
    file_path: str,
    name: Optional[str],
    directory: str,
    properties: tuple,
):
    """Async implementation of upload command."""
    # Get settings from context or create new
    settings = ctx.obj if ctx.obj else get_settings()

    # Validate file path
    path = Path(file_path)
    if not path.exists():
        click.echo(f"Error: File not found: {file_path}", err=True)
        ctx.exit(1)

    if not path.is_file():
        click.echo(f"Error: Not a file: {file_path}", err=True)
        ctx.exit(1)

    # Parse properties
    metadata = {"directory": directory}
    for prop in properties:
        if "=" not in prop:
            click.echo(
                f"Error: Invalid property format: {prop}. Use key=value", err=True
            )
            ctx.exit(1)
        key, value = prop.split("=", 1)
        metadata[key.strip()] = value.strip()

    # Use filename if name not provided
    asset_name = name if name else path.name

    async with NexusClient(
        base_url=settings.host,
        username=settings.username,
        password=settings.password,
        timeout=settings.timeout,
        verify_ssl=settings.verify_ssl,
    ) as client:
        try:
            click.echo(f"Uploading {path.name} to {repository}...")
            click.echo(f"  Asset name: {asset_name}")
            click.echo(f"  Directory: {directory}")
            if len(properties) > 0:
                click.echo(f"  Properties: {dict((k, metadata[k]) for k in metadata if k != 'directory')}")

            response = await client.upload_component(
                repository=repository,
                file_path=path,
                asset_name=asset_name,
                **metadata,
            )

            click.echo(f"\nSuccessfully uploaded to {repository}{directory}{asset_name}")

        except FileNotFoundError as e:
            click.echo(f"Error: {e}", err=True)
            ctx.exit(1)
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            ctx.exit(1)
