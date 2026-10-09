"""Bot settings, read from environment variables (a .env file is loaded first, if present)."""

from __future__ import annotations

import logging
import logging.config
import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Log file path
LOG_FOLDER_PATH = BASE_DIR / 'logs'
LOG_FOLDER_PATH.mkdir(parents=True, exist_ok=True)
CONFIG_FOLDER_PATH = BASE_DIR / 'config'

# Database file path
DB_PATH = BASE_DIR / 'instance'
DB_PATH.mkdir(parents=True, exist_ok=True)
DB_PATH = 'sqlite:///' + str(BASE_DIR / 'instance' / 'word_counter.db')

# Cog folder path
COG_FOLDER_PATH = BASE_DIR / 'cogs'

TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off", ""}


class ConfigError(Exception):
    """Raised when a setting is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    # The token is left out of repr so it never ends up in a log line.
    token: str = field(repr=False)
    guild_id: int
    welcome_channel_id: int | None
    admin_ids: frozenset[int]
    scan_history: bool


def load_settings() -> Settings:
    """Read and validate all settings. Raises ConfigError with a readable message."""
    welcome_channel = os.environ.get("WELCOME_CHANNEL_ID", "").strip()
    return Settings(
        token=_required("DISCORD_TOKEN"),
        guild_id=_parse_id("GUILD_ID", _required("GUILD_ID")),
        welcome_channel_id=_parse_id("WELCOME_CHANNEL_ID", welcome_channel) if welcome_channel else None,
        admin_ids=frozenset(
            _parse_id("ADMIN_IDS", part)
            for part in os.environ.get("ADMIN_IDS", "").replace(" ", "").split(",")
            if part
        ),
        scan_history=_parse_bool("SCAN_HISTORY", os.environ.get("SCAN_HISTORY", "")),
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


def _parse_bool(name: str, raw: str) -> bool:
    value = raw.strip().lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    raise ConfigError(f"{name} must be true or false, got {raw!r}.")


class CustomFormatter(logging.Formatter):
    """
    Custom formatter to add colors to log messages.
    """
    COLORS = {
        'DEBUG': '\033[37m',       # White
        'INFO': '\033[32m',        # Green
        'WARNING': '\033[33m',     # Yellow
        'ERROR': '\033[31m',       # Red
        'CRITICAL': '\033[1;31m',  # Bold Red
        'NAME': '\033[36m'         # Cyan
    }
    RESET = '\033[0m'

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        name_color = self.COLORS['NAME']
        record.levelname = f"{log_color}{record.levelname:<8}{self.RESET}"
        record.name = f"{name_color}{record.name}{self.RESET}"
        record.msg = f"{log_color}{record.msg}{self.RESET}"
        return super().format(record)


def setup_logging():
    """
    Sets up the logging configuration for the application.

    Reads the logging configuration from a YAML file and applies it.
    Updates the log file paths for rotating and error logs.
    """
    try:
        with open(CONFIG_FOLDER_PATH / 'logging_config.yaml', 'r') as file:
            config = yaml.safe_load(file.read())

        # Update file paths
        config['handlers']['rotating_file']['filename'] = str(LOG_FOLDER_PATH / 'bot.log')
        config['handlers']['error_file']['filename'] = str(LOG_FOLDER_PATH / 'errors.log')

        logging.config.dictConfig(config)
    except FileNotFoundError:
        logging.error(f"Logging configuration not found: {CONFIG_FOLDER_PATH / 'logging_config.yaml'}")
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in Logging Configuration: {e}")
