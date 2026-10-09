"""Colored console logging plus rotating log files in ./logs."""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TextIO

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_FORMAT = "%(asctime)s [%(levelname)-8s] [%(name)-15s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_LOG_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 5

# Library loggers that get noisy below these levels.
# discord.http logs every request payload at DEBUG, including message content.
LIBRARY_MIN_LEVELS = {
    "discord": logging.INFO,
    "sqlalchemy": logging.WARNING,
    "asyncio": logging.WARNING,
}

RESET = "\033[0m"
GREY = "\033[90m"
CYAN = "\033[36m"
LEVEL_COLORS = {
    logging.DEBUG: "\033[37m",  # White
    logging.INFO: "\033[32m",  # Green
    logging.WARNING: "\033[33m",  # Yellow
    logging.ERROR: "\033[31m",  # Red
    logging.CRITICAL: "\033[1;31m",  # Bold red
}


class ColorFormatter(logging.Formatter):
    """Colors each part of the line without touching the record.

    The record is shared by every handler, so changing record.levelname or
    record.msg here would leak escape codes into the log files.
    """

    def __init__(self) -> None:
        super().__init__()
        self._formatters = {
            level: logging.Formatter(
                f"{GREY}%(asctime)s{RESET} "
                f"{color}[%(levelname)-8s]{RESET} "
                f"{CYAN}[%(name)-15s]{RESET} "
                f"{color}%(message)s{RESET}",
                DATE_FORMAT,
            )
            for level, color in LEVEL_COLORS.items()
        }

    def format(self, record: logging.LogRecord) -> str:
        formatter = self._formatters.get(record.levelno, self._formatters[logging.DEBUG])
        return formatter.format(record)


def setup_logging() -> None:
    """Configure the root logger. Reads LOG_LEVEL from the environment (default INFO)."""
    level_name = os.environ.get("LOG_LEVEL", "INFO").strip().upper()
    known_level = logging.getLevelNamesMapping().get(level_name)
    level = logging.INFO if known_level is None else known_level

    root = logging.getLogger()
    root.setLevel(level)
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()

    console = logging.StreamHandler(sys.stdout)
    if _stream_supports_color(sys.stdout):
        console.setFormatter(ColorFormatter())
    else:
        console.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root.addHandler(console)

    file_error = _add_file_handlers(root)

    for name, min_level in LIBRARY_MIN_LEVELS.items():
        logging.getLogger(name).setLevel(max(level, min_level))

    logging.captureWarnings(True)

    if known_level is None:
        logging.getLogger(__name__).warning("Unknown LOG_LEVEL %r; using INFO.", level_name)
    if file_error:
        logging.getLogger(__name__).warning("Logging to the console only: %s", file_error)


def _add_file_handlers(root: logging.Logger) -> OSError | None:
    """Add bot.log (everything) and errors.log (ERROR and up).

    Returns the error if the log folder is not writable.
    """
    plain = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        for filename, file_level in (("bot.log", logging.NOTSET), ("errors.log", logging.ERROR)):
            handler = RotatingFileHandler(
                LOG_DIR / filename,
                maxBytes=MAX_LOG_BYTES,
                backupCount=LOG_BACKUP_COUNT,
                encoding="utf-8",
            )
            handler.setLevel(file_level)
            handler.setFormatter(plain)
            root.addHandler(handler)
    except OSError as exc:
        return exc
    return None


def _stream_supports_color(stream: TextIO) -> bool:
    # https://no-color.org and the FORCE_COLOR convention.
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    if not stream.isatty():
        return False
    if sys.platform == "win32":
        return _enable_windows_ansi()
    return True


def _enable_windows_ansi() -> bool:
    """The classic Windows console needs ANSI handling switched on before colors work."""
    import ctypes
    from ctypes import wintypes

    enable_virtual_terminal_processing = 0x0004
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
    mode = wintypes.DWORD()
    if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        return False
    if mode.value & enable_virtual_terminal_processing:
        return True
    return bool(kernel32.SetConsoleMode(handle, mode.value | enable_virtual_terminal_processing))
