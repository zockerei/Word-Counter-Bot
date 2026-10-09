"""Finding tracked words in messages, live and in the server history."""

from __future__ import annotations

import asyncio
import logging
import re
from collections import Counter
from dataclasses import dataclass, field

import discord
from unidecode import unidecode

logger = logging.getLogger('bot.counting')

# Discord rate-limits message history per channel, so channels are read in parallel.
# A few at a time is enough to be much faster without hitting the global rate limit.
PARALLEL_CHANNELS = 5


def normalize(text: str) -> str:
    """Lowercase ASCII, so 'Café' and 'CAFE' both match the word 'cafe'."""
    return unidecode(text).lower().strip()


def compile_patterns(words: list[str]) -> dict[str, re.Pattern]:
    """One regex per word that only matches whole words, so 'gay' doesn't match 'gayle'."""
    return {word: re.compile(r'\b' + re.escape(word) + r'\b') for word in words}


def count_words(text: str, patterns: dict[str, re.Pattern]) -> dict[str, int]:
    """How often each tracked word appears in the text. Words that don't appear are left out."""
    text = normalize(text)
    counts = {}
    for word, pattern in patterns.items():
        amount = len(pattern.findall(text))
        if amount:
            counts[word] = amount
    return counts


@dataclass
class ScanResult:
    # (user_id, word) -> count
    counts: Counter[tuple[int, str]] = field(default_factory=Counter)
    messages: int = 0


async def scan_history(guild: discord.Guild, patterns: dict[str, re.Pattern]) -> ScanResult:
    """Count the words in every message the bot can read, including threads and forum posts."""
    result = ScanResult()
    channels = await _readable_channels(guild)
    logger.info('Scanning %s channels and threads for %s word(s)', len(channels), len(patterns))
    semaphore = asyncio.Semaphore(PARALLEL_CHANNELS)

    async def scan(channel: discord.TextChannel | discord.Thread) -> None:
        async with semaphore:
            messages = 0
            try:
                async for message in channel.history(limit=None):
                    messages += 1
                    if message.author.bot:
                        continue
                    for word, amount in count_words(message.content, patterns).items():
                        result.counts[message.author.id, word] += amount
            except discord.HTTPException as exc:
                logger.warning('Could not read all of #%s: %s', channel.name, exc)
            result.messages += messages
            logger.debug('Scanned #%s: %s messages', channel.name, messages)

    await asyncio.gather(*(scan(channel) for channel in channels))
    logger.info('Scan finished: %s messages', result.messages)
    return result


async def _readable_channels(guild: discord.Guild) -> list[discord.TextChannel | discord.Thread]:
    """Text channels plus their active and archived threads, skipping what the bot can't read."""
    channels = []
    for parent in [*guild.text_channels, *guild.forums]:
        permissions = parent.permissions_for(guild.me)
        if not (permissions.view_channel and permissions.read_message_history):
            continue
        if isinstance(parent, discord.TextChannel):
            channels.append(parent)
        channels.extend(parent.threads)
        try:
            channels.extend([thread async for thread in parent.archived_threads(limit=None)])
        except discord.HTTPException as exc:
            logger.warning('Could not list the archived threads of #%s: %s', parent.name, exc)
    return channels
