"""Discord bot that counts how often each member says the tracked words."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import re
import signal
from collections.abc import Coroutine

import discord
from discord import Color, Embed, app_commands
from dotenv import load_dotenv

import commands
from config import ConfigError, Settings, load_settings
from counting import ScanResult, compile_patterns, count_words, scan_history
from database import Database
from logging_config import setup_logging

logger = logging.getLogger('bot')

# The bot never joins voice, so don't warn about missing voice dependencies.
discord.VoiceClient.warn_nacl = False
discord.VoiceClient.warn_dave = False


class WordCounterBot(discord.Client):
    def __init__(self, settings: Settings, db: Database) -> None:
        # Message content to count words, members for the welcome message.
        # Both are privileged intents and have to be turned on in the Developer Portal.
        intents = discord.Intents(
            guilds=True, guild_messages=True, message_content=True, members=True
        )
        # Messages are counted once and never looked up again, so don't cache them.
        super().__init__(intents=intents, max_messages=None)
        self.settings = settings
        self.db = db
        self.tree = app_commands.CommandTree(self)
        commands.register(self.tree)
        self.patterns: dict[str, re.Pattern] = {}
        self._tasks: set[asyncio.Task] = set()

    async def setup_hook(self) -> None:
        # setup_hook runs once, unlike on_ready, which fires again after reconnects.
        await self.reload_words()
        guild = discord.Object(id=self.settings.guild_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        logger.info('Slash commands synced')
        if self.settings.scan_history:
            self.run_in_background(self._scan_on_startup())

    async def reload_words(self) -> None:
        self.patterns = compile_patterns(await self.db.get_words())
        logger.info('Tracking %s word(s)', len(self.patterns))

    def run_in_background(self, coro: Coroutine) -> None:
        task = asyncio.create_task(coro)
        # Keep a reference, or the task can be garbage collected while it runs.
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def count_history(self, words: list[str]) -> ScanResult:
        """Scan the whole server for these words and store the counts."""
        await self.wait_until_ready()
        guild = self.get_guild(self.settings.guild_id)
        result = await scan_history(guild, compile_patterns(words))
        await self.db.raise_counts(result.counts)
        return result

    async def _scan_on_startup(self) -> None:
        try:
            await self.count_history(list(self.patterns))
        except Exception:
            logger.exception('Scanning the history failed')

    async def on_ready(self) -> None:
        logger.info('Logged in as %s', self.user)
        if self.get_guild(self.settings.guild_id) is None:
            logger.warning('The bot is not in the server %s', self.settings.guild_id)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        if message.guild.id != self.settings.guild_id:
            return
        for word, amount in count_words(message.content, self.patterns).items():
            total = await self.db.add_count(message.author.id, word, amount)
            logger.info('%s said "%s" (%s in total)', message.author, word, total)
            if total == amount:
                await message.channel.send(embed=Embed(
                    title='First time 😩',
                    description=f'{message.author.display_name} was a naughty boy and said {word}\n'
                                f'His first time... 💦',
                    color=Color.red(),
                ))

    async def on_member_join(self, member: discord.Member) -> None:
        if member.guild.id != self.settings.guild_id or not self.settings.welcome_channel_id:
            return
        channel = self.get_channel(self.settings.welcome_channel_id)
        if channel is None:
            logger.warning('Welcome channel %s not found', self.settings.welcome_channel_id)
            return
        await channel.send(embed=Embed(
            title='A new victim',
            description=f'A new victim joined the Server\n'
                        f'Be aware of what you type {member.mention}... 😳',
            color=Color.blue(),
        ).set_footer(text=', '.join(self.patterns)))

    async def close(self) -> None:
        for task in self._tasks:
            task.cancel()
        await super().close()


async def run(settings: Settings) -> None:
    db = Database(settings.database_url)
    try:
        await db.init()
        async with WordCounterBot(settings, db) as bot:
            # docker stop sends SIGTERM. Shut down cleanly instead of being killed.
            # Windows has no signal handlers in asyncio; Ctrl+C still works there.
            with contextlib.suppress(NotImplementedError):
                asyncio.get_running_loop().add_signal_handler(
                    signal.SIGTERM, lambda: asyncio.create_task(bot.close())
                )
            await bot.start(settings.token)
    finally:
        await db.close()


def main() -> None:
    load_dotenv()
    setup_logging()
    try:
        settings = load_settings()
    except ConfigError as exc:
        logger.critical('%s', exc)
        raise SystemExit(1) from None

    try:
        asyncio.run(run(settings))
    except KeyboardInterrupt:
        pass
    except discord.LoginFailure:
        logger.critical('Discord rejected the token. Check DISCORD_TOKEN.')
        raise SystemExit(1) from None
    except discord.PrivilegedIntentsRequired:
        logger.critical(
            'Enable the Message Content and Server Members intents for the bot '
            'in the Discord Developer Portal.'
        )
        raise SystemExit(1) from None
    except Exception:
        logger.critical('The bot stopped because of an unhandled error.', exc_info=True)
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
