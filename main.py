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
    channel_id = bot_config['channel_id']
bot_logger.info('bot_config loaded')


def convert_id(mention):
    """get user id from message"""

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
    sql_statements.create_tables()
    sql_statements.add_words(words)

    # get server member ids and add them all to the database
    bot_logger.debug('Insert all guild members')
    guild_members = client.get_guild(server_id).members
    guild_member_ids = [member.id for member in guild_members]
    bot_logger.debug(f'Server member ids: {guild_member_ids}')
    sql_statements.add_user_ids(*guild_member_ids)
    bot_logger.info('Bot ready')


@client.event
async def on_member_join(member):
    """create new User in database if member joins"""
    bot_logger.debug(f'{member} joined')

    # create new user in database
    sql_statements.add_user_ids(*member.id)

    # create embed for new user
    username = await client.fetch_user(member.id)
    new_user_embed = embed.Embed(
        client.user.avatar,
        title=f'A new victim'
    )
    new_user_embed.add_description(
        f"""A new victim joined the Server\n
        Be aware of what you type {username}... :flushed:"""
    )
    channel = client.get_channel(channel_id)
    await channel.send(embed=new_user_embed)
    bot_logger.debug(f'New user message sent')


@client.event
async def on_message(message):
    """All events with messages (count, highest count, word counter)"""
    if message.author == client.user:
        # message comes from bot
        bot_logger.debug('Bot message')
        return

    message_content = message.content.lower()

    if message_content.startswith('/c' or '/count'):
        """get count of user with word"""
        bot_logger.info('Get count of user with word')

        # split message
        message_split = message_content.split(' ')
        word = message_split[1]
        converted_user_id = convert_id(message_split[2])

        # convert and get username
        count_user_id = sql_statements.get_counts(converted_user_id, word)
        username = await client.fetch_user(converted_user_id)

        if count_user_id == -1:
            # create embed for 0 count user
            bot_logger.debug(f'Creating embed for zero count for username: {username}')
            zero_count_embed = embed.Embed(
                client.user.avatar,
                title=f'{username} is clean'
            )
            zero_count_embed.add_description(
                f'{username} has said {word} 0 times\n (Or he tricked the system)'
            )
            await message.channel.send(embed=zero_count_embed)
            return

        # send message with count
        bot_logger.debug('Creating count embed')
        count_embed = embed.Embed(
            client.user.avatar,
            title=f'Count from {username}'
        )
        count_embed.add_description(f'{username} has said {word} {count_user_id} times')

        # set footer
        highest_count_tuple = sql_statements.get_highest_count_column(word)
        username = await client.fetch_user(highest_count_tuple[0])
        count_embed.add_footer(
            f'The person who has said {word} the most is '
            f'{username} with {highest_count_tuple[2]} times'
        )
        await message.channel.send(embed=count_embed)
        bot_logger.debug('Count message sent')

        return

    if message_content.startswith('/hc' or '/highestCount'):
        """get the highest count from all users from word"""
        # get the highest count
        bot_logger.debug('Get highest count of user from word')
        word = message_content.split(' ')[1]
        highest_count_tuple = sql_statements.get_highest_count_column(word)

        if highest_count_tuple is None:
            # make embed when no user has said the word
            bot_logger.debug(f'Creating embed. No User has said the word: {word}')
            no_count_embed = embed.Embed(
                client.user.avatar,
                title=f'Dead Server'
            )
            no_count_embed.add_description(
                f"""No User in this Server has said {word}\n
                This is very sospechoso... :sus:"""
            )
            await message.channel.send(embed=no_count_embed)
            return

        # make embed
        highest_count_embed = embed.Embed(
            client.user.avatar,
            title=f'Highest count from all Users'
        )
        username = await client.fetch_user(highest_count_tuple[0])
        highest_count_embed.add_description(
            f"""The user who has said {word} the most is ||{username}||\n
            With an impressive amount of {highest_count_tuple[2]} times"""
        )
        await message.channel.send(embed=highest_count_embed)
        bot_logger.debug('Highest count message sent')
        return

    if message_content.startswith('/thc' or '/totalHighestCount'):
        """get the user with highest amount of all words"""
        bot_logger.debug('Get user with highest amount of all words')
        total_highest_count = sql_statements.get_total_highest_count_column()

        if total_highest_count is None:
            # make embed when no user has said the word
            bot_logger.debug(f'Creating embed. No User has said the any word')
            no_count_embed = embed.Embed(
                client.user.avatar,
                title=f'Dead Server'
            )
            no_count_embed.add_description(
                f"""No User in this Server has said any word...\n
                This is very sospechoso... :sus:"""
            )
            await message.channel.send(embed=no_count_embed)
            return

        # make embed
        bot_logger.debug('Making thc_embed')
        username = await client.fetch_user(total_highest_count[0])
        thc_embed = embed.Embed(
            client.user.avatar,
            title=f'Highest count of all words'
        )
        thc_embed.add_description(
            f"""The winner for the Highest count of all words is.... ||{username}!||\n
            Who has said {total_highest_count[1]} {total_highest_count[2]} times"""
        )
        thc_embed.add_footer(
            f'Imagine'
        )
        await message.channel.send(embed=thc_embed)
        bot_logger.info('Message for total highest count sent')
        return

    # check if message has any word
    for word in words:
        if word in message_content:
            # add words count to database
            bot_logger.info(f'Word: {word} found in message')
            word_count = message_content.count(word)
            user_id = message.author.id

            # see if it is the first time the User has said the word
            if sql_statements.get_counts(user_id, word) is None:
                bot_logger.debug(f'First time {user_id} has said {word}')
                sql_statements.update_user_count(user_id, word, word_count)

                # first time embed
                username = await client.fetch_user(user_id)
                first_time_embed = embed.Embed(
                    client.user.avatar,
                    title=f'First time :smirk:'
                )
                first_time_embed.add_description(
                    f"""{username} was a naughty boy and said {word}\n
                    His first time... :sweat_drops:"""
                )
                await message.channel.send(embed=first_time_embed)
                bot_logger.debug('First time message sent')
        else:
            bot_logger.info(f'Word: {word} not found in message')


client.run(token, log_handler=None)
