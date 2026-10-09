"""Bot settings, read from environment variables (a .env file is loaded first, if present)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from database import asyncpg_url

TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off", ""}


class ConfigError(Exception):
    """Raised when a setting is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    # Secrets are left out of repr so they never end up in a log line.
    token: str = field(repr=False)
    guild_id: int
    welcome_channel_id: int | None
    scan_history: bool
    database_url: str = field(repr=False)


def load_settings() -> Settings:
    """Read and validate all settings. Raises ConfigError with a readable message."""
    welcome_channel = os.environ.get("WELCOME_CHANNEL_ID", "").strip()
    return Settings(
        token=_required("DISCORD_TOKEN"),
        guild_id=_parse_id("GUILD_ID", _required("GUILD_ID")),
        welcome_channel_id=(
            _parse_id("WELCOME_CHANNEL_ID", welcome_channel) if welcome_channel else None
        ),
        scan_history=_parse_bool("SCAN_HISTORY", os.environ.get("SCAN_HISTORY", "")),
        database_url=_parse_database_url(_required("DATABASE_URL")),
    )


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(f"Missing {name}. Copy .env.example to .env and fill it in.")
    return value


def _parse_id(name: str, raw: str) -> int:
    if not raw.isdigit():
        raise ConfigError(f"{name} must be a Discord ID (a number), got {raw!r}.")
    return int(raw)


def _parse_database_url(raw: str) -> str:
    try:
        asyncpg_url(raw)
    except ValueError as exc:
        raise ConfigError(f"DATABASE_URL is not valid: {exc}.") from None
    return raw


def _parse_bool(name: str, raw: str) -> bool:
    value = raw.strip().lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    raise ConfigError(f"{name} must be true or false, got {raw!r}.")
