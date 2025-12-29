"""Main CLI application."""

import click

from nexus_cli import __version__
from nexus_cli.commands.download import download
from nexus_cli.commands.list import list_assets
from nexus_cli.commands.search import search
from nexus_cli.commands.upload import upload
from nexus_cli.config import get_settings


@click.group()
@click.version_option(version=__version__, prog_name="nexus")
@click.option(
    "--host",
    envvar="NEXUS_HOST",
    help="Nexus server URL (default: from config or env)",
)
@click.option(
    "--username",
    envvar="NEXUS_USER",
    help="Nexus username for authentication",
)
@click.option(
    "--password",
    envvar="NEXUS_PASS",
    help="Nexus password for authentication",
)
@click.option(
    "--timeout",
    type=int,
    envvar="NEXUS_TIMEOUT",
    help="Request timeout in seconds (default: 30)",
)
@click.option(
    "--no-verify-ssl",
    is_flag=True,
    help="Disable SSL certificate verification",
)
@click.pass_context
def main(ctx, host, username, password, timeout, no_verify_ssl):
    """Nexus Repository Manager CLI Tool.

    A command-line interface for interacting with Nexus Repository Manager.
    Supports searching, downloading, and uploading artifacts.

    \b
    Configuration:
    - Settings can be provided via CLI options, environment variables, or config file
    - Config file location: ~/.nexus/config.toml
    - Environment variables: NEXUS_HOST, NEXUS_USER, NEXUS_PASS, NEXUS_TIMEOUT

    \b
    Examples:
        nexus search --repository maven-releases --name myapp
        nexus download --repository raw-hosted --asset-path /data/file.txt --output ./
        nexus upload --repository raw-hosted --file ./myfile.txt
    """
    # Prepare overrides from CLI options
    overrides = {}
    if host:
        overrides["host"] = host
    if username:
        overrides["username"] = username
    if password:
        overrides["password"] = password
    if timeout:
        overrides["timeout"] = timeout
    if no_verify_ssl:
        overrides["verify_ssl"] = False

    # Store settings in context for commands
    ctx.obj = get_settings(**overrides)


# Register commands
main.add_command(search)
main.add_command(list_assets)
main.add_command(download)
main.add_command(upload)


if __name__ == "__main__":
    main()
