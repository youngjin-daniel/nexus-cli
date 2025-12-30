"""Main CLI application."""

import click

from nexus import __version__
from nexus.commands.download import download
from nexus.commands.search import search
from nexus.commands.upload import upload
from nexus.config import get_settings


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
    "--repository",
    "-r",
    envvar="NEXUS_REPOSITORY",
    help="Default repository name (default: from NEXUS_REPOSITORY env or 'my-repo')",
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
def main(ctx, host, repository, username, password, timeout, no_verify_ssl):
    """Nexus Repository Manager CLI Tool.

    A command-line interface for interacting with Nexus Repository Manager.
    Supports searching, downloading, and uploading artifacts.

    \b
    Configuration:
    - Settings MUST be provided via CLI options or environment variables
    - Required: NEXUS_HOST, NEXUS_REPOSITORY
    - Optional: NEXUS_USER, NEXUS_PASS, NEXUS_TIMEOUT

    \b
    Examples:
        nexus --host https://nexus.example.com -r my-repo search -p "MyProject/build_*artifact.zip"
        nexus download -p "MyProject/build_*artifact.zip" -o ./downloads
        nexus upload --repository raw-hosted --file ./myfile.txt
    """
    # Prepare overrides from CLI options
    overrides = {}
    if host:
        overrides["host"] = host
    if repository:
        overrides["repository"] = repository
    if username:
        overrides["username"] = username
    if password:
        overrides["password"] = password
    if timeout:
        overrides["timeout"] = timeout
    if no_verify_ssl:
        overrides["verify_ssl"] = False

    # Store settings in context for commands
    try:
        ctx.obj = get_settings(**overrides)
    except ValueError as e:
        click.echo(f"Configuration Error: {e}", err=True)
        ctx.exit(1)


# Register commands
main.add_command(search)
main.add_command(download)
main.add_command(upload)


if __name__ == "__main__":
    main()
