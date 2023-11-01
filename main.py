import discord
import logging.config
import yaml
import sql

sql_statements = sql.SqlStatements()

# import logging_config
with open('logging_config.yaml', 'rt') as config_file:
    logging_config = yaml.safe_load(config_file.read())

# logging setup
logging.config.dictConfig(logging_config)
discord_logger = logging.getLogger('discord')
bot_logger = logging.getLogger('bot.main')
bot_logger.debug('Logging setup complete')

# intents
intents = discord.Intents.all()
client = discord.Client(intents=intents)

# load json
with open('bot_config.yaml') as config_file:
    bot_config = yaml.safe_load(config_file.read())
    token = bot_config['token']
    word = bot_config['word']
    server_id = bot_config['server_id']
bot_logger.debug('bot_config loaded')


def convert_mention(mention):
    """convert mention user_id to normal user_id"""
    bot_logger.debug('converting mention')
    mention = mention.replace('<', '')
    mention = mention.replace('>', '')
    mention = mention.replace('@', '')
    bot_logger.debug(f'Mention converted to user_id: {mention}')
    return mention


@client.event
async def on_ready():
    """Login and database setup"""
    bot_logger.info(f'Logged in as {client.user}')
    sql_statements.create_table()

    # get server member ids and add them all to the database
    bot_logger.debug('Insert all guild members')
    guild_members = client.get_guild(server_id).members
    guild_member_ids = [member.id for member in guild_members]
    bot_logger.debug(f'Server member ids: {guild_member_ids}')
    sql_statements.add_guild_members(guild_member_ids)
    bot_logger.info('All members in database')
    bot_logger.info('Bot ready')


@client.event
async def on_message(message):
    """All events with messages"""
    if message.author == client.user:
        # message comes from bot
        bot_logger.debug('Bot message')
        return

    message_content = message.content.lower()

    if message_content.startswith('/c'):
        # get count of user
        bot_logger.info('Get count of user')
        converted_user_id = convert_mention(message_content.split(' ')[1])
        count_user_id = sql_statements.get_count(converted_user_id)
        username = await client.fetch_user(converted_user_id)
        await message.channel.send(f'{username} has said {word} {count_user_id} times')
        return

    # check if message has word
    if word not in message_content:
        bot_logger.info('Word not found in message')
        return

    # add word count to database
    bot_logger.info('Word found in message')
    word_count = message_content.count(word)
    user_id = message.author.id
    sql_statements.update_user_count(user_id, word_count)

client.run(token, log_handler=None)
