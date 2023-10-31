import discord
import logging.config
import yaml
import sql

# import logging_config
with open('logging_config.yaml', 'rt') as config_file:
    logging_config = yaml.safe_load(config_file.read())

sql_statements = sql.SqlStatements()

# logging setup
logging.config.dictConfig(logging_config)
discord_logger = logging.getLogger('discord')
bot_logger = logging.getLogger('bot.main')
bot_logger.debug('logging setup complete')

# intents
intents = discord.Intents.all()
client = discord.Client(intents=intents)

# load json
with open('bot_config.yaml') as config_file:
    bot_config = yaml.safe_load(config_file.read())
    token = bot_config['token']
    word = bot_config['word']
bot_logger.debug('bot_config loaded')


@client.event
async def on_ready():
    """Login and database setup"""
    bot_logger.info(f'Logged in as {client.user}')
    sql_statements.create_table()


@client.event
async def on_message(message):
    """Check message for the word and add it to the database"""
    if message.author == client.user:
        bot_logger.info('message is from author')
        return

    message_content = message.content.lower()
    if word not in message_content:
        bot_logger.info('word not found in message')
        return

    bot_logger.info('word found in message')
    count = message_content.count(word)
    user_id = message.author.id
    sql_statements.insert_update_user_count(user_id, count)

client.run(token, log_handler=None)
