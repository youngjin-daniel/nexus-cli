"""Configuration settings management."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Settings:
    """Configuration settings for Nexus CLI.

    Priority (highest to lowest):
    1. Explicitly provided values
    2. Environment variables

    Required settings: host, repository
    """

    host: str
    repository: str
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    verify_ssl: bool = True

    @classmethod
    def from_env(cls, **overrides) -> "Settings":
        """Create settings from environment variables.

        Args:
            **overrides: Explicit values that override all other sources

        Returns:
            Settings instance

        Raises:
            ValueError: If required settings (host, repository) are not provided
        """
        # Merge settings with priority: overrides > env
        host = overrides.get("host") or os.getenv("NEXUS_HOST")
        repository = overrides.get("repository") or os.getenv("NEXUS_REPOSITORY")

        # Validate required settings
        if not host:
            raise ValueError(
                "NEXUS_HOST is required. "
                "Set via --host option or NEXUS_HOST environment variable."
            )
        if not repository:
            raise ValueError(
                "NEXUS_REPOSITORY is required. "
                "Set via --repository option or NEXUS_REPOSITORY environment variable."
            )

        settings = {
            "host": host,
            "repository": repository,
            "username": overrides.get("username") or os.getenv("NEXUS_USER"),
            "password": overrides.get("password") or os.getenv("NEXUS_PASS"),
            "timeout": int(
                overrides.get("timeout") or os.getenv("NEXUS_TIMEOUT") or 30
            ),
            "verify_ssl": _str_to_bool(
                overrides.get("verify_ssl")
                if "verify_ssl" in overrides
                else os.getenv("NEXUS_VERIFY_SSL")
                or True
            ),
        }

        return cls(**settings)


def _str_to_bool(value) -> bool:
    """Convert string or other value to boolean.

    Args:
        value: Value to convert

    Returns:
        Boolean representation
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() not in ("false", "0", "no", "")
    return bool(value)


def get_settings(**overrides) -> Settings:
    """Get settings instance.

    Args:
        **overrides: Explicit values that override all other sources

    Returns:
        Settings instance
    """
    return Settings.from_env(**overrides)
