import argparse
import discord
import logging.config
import yaml
import sql
import embed

sql_statements = sql.SqlStatements()

# import logging_config
with open('logging_config.yaml', 'rt') as config_file:
    logging_config = yaml.safe_load(config_file.read())

# logging setup
logging.config.dictConfig(logging_config)
discord_logger = logging.getLogger('discord')
bot_logger = logging.getLogger('bot.main')
bot_logger.debug('Logging setup complete')

# argument parser
bot_logger.debug('Setting up argument parser')
parser = argparse.ArgumentParser(description='Word-Counter-Bot')

parser.add_argument(
    '-p', '--path',
    help='Path to config file .yaml',
    required=True
)

config_path = parser.parse_args().path
bot_logger.debug('Got arguments successfully')

# intents
intents = discord.Intents.all()
client = discord.Client(intents=intents)

# load json
with open(config_path) as config_file:
    bot_config = yaml.safe_load(config_file.read())
    token = bot_config['token']
    words = bot_config['word']
    server_id = bot_config['server_id']
bot_logger.info('bot_config loaded')


def get_convert_id(message):
    """get user id from message"""
    bot_logger.debug('Split message mention')
    mention = message.split(' ')[1]

    bot_logger.debug('Convert message')
    mention = mention.replace('<', '')
    mention = mention.replace('>', '')
    mention = mention.replace('@', '')
    bot_logger.debug(f'Mention converted to user_id: {mention}')
    return mention


@client.event
async def on_ready():
    """Login and database setup"""
    bot_logger.info(f'Logged in as {client.user}')

    # create sql table and add words
    sql_statements.create_table()
    sql_statements.add_words(words)

    # get server member ids and add them all to the database
    bot_logger.debug('Insert all guild members')
    guild_members = client.get_guild(server_id).members
    guild_member_ids = [member.id for member in guild_members]
    bot_logger.debug(f'Server member ids: {guild_member_ids}')
    sql_statements.add_guild_members(guild_member_ids)
    bot_logger.info('Bot ready')


@client.event
async def on_message(message):
    """All events with messages (count, highest count, word counter)"""
    if message.author == client.user:
        # message comes from bot
        bot_logger.debug('Bot message')
        return

    message_content = message.content.lower()

    if message_content.startswith('/c' or '/count'):
        """get count of user"""

        bot_logger.info('Get count of user')
        converted_user_id = get_convert_id(message_content)
        count_user_id = sql_statements.get_count(converted_user_id)
        username = await client.fetch_user(converted_user_id)

        # send message with count
        bot_logger.debug('Creating count embed')
        count_embed = embed.EmbedBuilder(
            client.user.avatar,
            title=f'Count from {username}'
        )
        count_embed.add_description(f'{username} has said {word} {count_user_id} times')
        await message.channel.send(embed=count_embed)
        bot_logger.debug('Count message sent')

        return

    if message_content.startswith('/hc' or '/highestCount'):
        """get the highest count from all users"""

        # get the highest count
        bot_logger.debug('Get highest count of user')
        highest_count_tuple = sql_statements.get_highest_count_tuple()

        # make embed
        highest_count_embed = embed.EmbedBuilder(
            client.user.avatar,
            title=f'Highest count from user'
        )
        username = await client.fetch_user(highest_count_tuple[0])
        highest_count_embed.add_description(
            f"""The user who has said {word} the most is ||{username}||\n
            With an impressive amount of {highest_count_tuple[1]} times"""
        )
        await message.channel.send(embed=highest_count_embed)
        bot_logger.debug('Highest count message sent')

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
