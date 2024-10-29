import discord
import logging.config
from config import setup_logging, COG_FOLDER_PATH, get_bot_config
from discord.ext import commands
import os
import asyncio

setup_logging()
bot_logger = logging.getLogger('bot')
bot_logger.info('Logging setup complete')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot_logger.info('Intents setup complete')

bot = commands.Bot(command_prefix='!', intents=intents)

config = get_bot_config()


async def main():
    """
    Loads all cog extensions and starts the Discord bot.
    """
    for filename in os.listdir(COG_FOLDER_PATH):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            bot_logger.debug(f'Loaded cog: {filename[:-3]}')
    await bot.start(config.token)

asyncio.run(main())
