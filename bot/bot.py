import discord
import logging.config
from config import setup_logging, load_bot_config, COG_FOLDER_PATH
from discord.ext import commands
import os

setup_logging()
bot_logger = logging.getLogger('bot')
bot_logger.info('Logging setup complete')

token, words, server_id, channel_id, admin_ids, disable_initial_scan = load_bot_config()

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot_logger.info('Intents setup complete')

bot = commands.Bot(command_prefix='!', intents=intents)

# Load cogs
for filename in os.listdir(COG_FOLDER_PATH):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')
        bot_logger.debug(f'Loaded cog: {filename[:-3]}')

bot.run(token, log_handler=None)
