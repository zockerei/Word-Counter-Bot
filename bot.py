import discord
import logging.config
from config import ConfigError, setup_logging, COG_FOLDER_PATH, load_settings
from database import Database
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()
setup_logging()
bot_logger = logging.getLogger('bot')
bot_logger.info('Logging setup complete')

try:
    settings = load_settings()
except ConfigError as exc:
    bot_logger.critical('%s', exc)
    raise SystemExit(1) from None

intents = discord.Intents.none()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
intents.members = True
bot_logger.info('Intents setup complete')

bot = commands.Bot(command_prefix='!', intents=intents)

bot.config = settings


async def main():
    """
    Opens the database, loads all cog extensions and starts the Discord bot.
    """
    bot.db = Database(settings.database_url)
    try:
        await bot.db.init()
        for filename in os.listdir(COG_FOLDER_PATH):
            if filename.endswith('.py'):
                await bot.load_extension(f'cogs.{filename[:-3]}')
        await bot.start(bot.config.token)
    finally:
        await bot.db.close()

asyncio.run(main())
