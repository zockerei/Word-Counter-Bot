# Requirements: python 3.11
# All imports below
import argparse
import discord
import logging.config
import yaml
import sql
import embed

COMMAND_PREFIXES = ('/c', '/hc', '/thc', '/sw', '/aw', '/rw')
sql_statements = sql.SqlStatements()

# Argument parser
parser = argparse.ArgumentParser(
    description="""Word-Counter-Bot for Discord.
    Needs the logging_config.yaml"""
)
parser.add_argument(
    '-p', '--path',
    help='Path to config file .yaml',
    required=True
)
config_path = parser.parse_args().path

# Logging setup
with open('logging_config.yaml', 'rt') as config_file:
    logging_config = yaml.safe_load(config_file.read())
    logging.config.dictConfig(logging_config)

discord_logger = logging.getLogger('discord')
bot_logger = logging.getLogger('bot.main')
bot_logger.info('Logging setup complete')

# Intents
intents = discord.Intents.all()
client = discord.Client(intents=intents)

# Load bot configuration
with open(config_path) as config_file:
    bot_config = yaml.safe_load(config_file)
    token, words, server_id, channel_id, admin_id = (
        bot_config['token'],
        bot_config['word'],
        bot_config['server_id'],
        bot_config['channel_id'],
        bot_config['admin_id']
    )
bot_logger.info('bot_config loaded')


@client.event
async def on_ready():
    """Handle the event when the bot is ready.

    This function logs in, sets up the database, adds words to the database,
    retrieves server member IDs and adds them to the database, and adds an admin user.
    """
    bot_logger.info(f'Logged in as {client.user}')

    # create sql table and add words
    sql_statements.create_tables()
    sql_statements.add_words(*words)

    # get server member ids and add them all to the database
    bot_logger.debug('Insert all guild members')
    guild_members = client.get_guild(server_id).members
    guild_member_ids = [member.id for member in guild_members]
    bot_logger.debug(f'Server member ids: {guild_member_ids}')
    sql_statements.add_user_ids(*guild_member_ids)

    # add admin user
    sql_statements.add_admin(admin_id)
    bot_logger.info('Bot ready')


@client.event
async def on_member_join(member: discord.Message):
    """Handle the event when a new member joins the server.

    This function adds the newly joined member to the database, creates an embed to welcome the new user,
    and sends the embed to the designated channel.

    Parameters:
        member (discord.Member): The member who joined the server.
    """
    bot_logger.debug(f'{member} joined')

    # create new user in database
    sql_statements.add_user_ids(member.id)

    # create embed for new user
    username = await client.fetch_user(member.id)
    new_user_embed = embed.Embed(
        client.user.avatar,
        title='A new victim'
    ).add_description(
        f"""A new victim joined the Server\n
        Be aware of what you type {username}... :flushed:"""
    ).add_footer(
        f'{sql_statements.get_words()}'
    )

    # send embed to the designated channel
    await client.get_channel(channel_id).send(embed=new_user_embed)
    bot_logger.info('New user message sent')


@client.event
async def on_message(message: discord.Message):
    """Handle the event when a message is received.

    This function processes all received messages, checks if they contain specific words,
    and performs corresponding actions such as updating word counts or handling commands.

    Parameters:
        message (discord.Message): The message received by the bot.
    """
    logging.debug('message from user or bot')
    if message.author == client.user:
        return  # Ignore messages from the bot

    for prefix in COMMAND_PREFIXES:
        if message.content.startswith(prefix):
            await handle_command(message, prefix)
            return
        else:
            bot_logger.debug(f'{prefix} not found in message')

    current_words = sql_statements.get_words()
    for word in current_words:
        if word in message.content.lower():
            await handle_word_count(message, word)
            return
        else:
            bot_logger.debug(f'{word} not found in message')


async def handle_command(message: discord.Message, prefix: str):
    """Handle all prefix commands.

    This function handles different commands based on the provided prefix.
    It then calls the corresponding command handler function.

    Parameters:
        message (discord.Message): The message containing the command.
        prefix (str): The command prefix used to trigger the command.
    """
    match prefix:
        case '/c':
            await handle_count_command(message)
            return
        case '/hc':
            await handle_highest_count_command(message)
            return
        case '/thc':
            await handle_total_highest_count_command(message)
            return
        case '/sw':
            await handle_show_words_command(message)
            return
        case '/aw':
            await handle_add_words_command(message)
            return
        case '/rw':
            await handle_remove_word_command(message)
            return


async def handle_count_command(message: discord.Message):
    """Handle the command to get the count of a specific word said by a user.

    This function retrieves the count of a specific word said by a user,
    creates an embed to display the count, and sends it to the channel.

    Parameters:
        message (discord.Message): The message containing the command.
    """
    bot_logger.debug('Get count of user with word')

    # split message
    _, word, user_id = message.content.lower().split(' ')
    converted_user_id = user_id.replace('<', '').replace('>', '').replace('@', '')

    # convert and get username
    count_user_id = sql_statements.get_count(converted_user_id, word)
    username = await client.fetch_user(converted_user_id)

    if count_user_id is None:
        # create embed for 0 count user
        bot_logger.debug(f'Creating embed for zero count for username: {username}')
        zero_count_embed = embed.Embed(
            client.user.avatar,
            title=f'{username} is clean'
        ).add_description(
            f"""{username} has said {word} 0 times\n
            (Or he tricked the system)"""
        )
        await message.channel.send(embed=zero_count_embed)

    # send message with count
    bot_logger.debug('Creating count embed')
    count_embed = embed.Embed(
        client.user.avatar,
        title=f'Count from {username}'
    ).add_description(
        f'{username} has said {word} {count_user_id} times'
    )

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


async def handle_highest_count_command(message: discord.Message):
    """Handle the command to get the highest count of a specific word from all users.

    This function retrieves the highest count of a specific word from all users,
    creates an embed to display the highest count, and sends it to the channel.

    Parameters:
        message (discord.Message): The message containing the command.
    """
    bot_logger.debug('Get highest count of user from word')
    word = message.content.lower().split(' ')[1]
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
            Or the word is not being monitored :eyes:"""
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
    bot_logger.info('Highest count message sent')
    return


async def handle_total_highest_count_command(message: discord.Message):
    """Handle the command to get the user with the highest count of all words.

    This function retrieves the user with the highest count of all words,
    creates an embed to display the user with the highest count, and sends it to the channel.

    Parameters:
        message (discord.Message): The message containing the command.
    """
    bot_logger.debug('Get user with highest amount of all words')
    total_highest_count = sql_statements.get_total_highest_count_column()

    if total_highest_count is None:
        # make embed when no user has said the word
        bot_logger.debug(f'Creating embed. No User has said any word')
        no_count_embed = embed.Embed(
            client.user.avatar,
            title=f'Dead Server'
        ).add_description(
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
    ).add_description(
        f"""The winner for the Highest count of all words is.... ||{username}!||\n
        Who has said {total_highest_count[1]} {total_highest_count[2]} times"""
    ).add_footer(
        f'Imagine'
    )
    await message.channel.send(embed=thc_embed)
    bot_logger.info('Message for total highest count sent')
    return


async def handle_show_words_command(message: discord.Message):
    """Handle the command to show all words from the database.

    This function retrieves all words from the database, creates an embed to display them,
    and sends the embed to the channel.

    Parameters:
        message (discord.Message): The message containing the command.
    """
    bot_logger.debug('Show all words from database')
    words_database = sql_statements.get_words()

    # create embed
    words_embed = embed.Embed(
        client.user.avatar,
        title=f'All words'
    ).add_description(
        f"""Here is a list of all the words you should rather not say...\n
        {', '.join(words_database)}"""
    )
    await message.channel.send(embed=words_embed)
    bot_logger.info('Message for all words sent')
    return


async def handle_add_words_command(message: discord.Message):
    """Handle the command to add words to the database.

    This function retrieves words from the command message, adds them to the database,
    creates an embed to confirm the addition, and sends it to the channel.

    Parameters:
        message (discord.Message): The message containing the command.
    """
    bot_logger.debug('Add words to database')

    # check if user has permission
    user_id = message.author.id
    if sql_statements.check_user_is_admin(user_id):
        # get words and add to database
        words_from_message = message.content.lower().split(' ')[1:]
        sql_statements.add_words(*words_from_message)

        # create embed for success
        add_words_embed = embed.Embed(
            client.user.avatar,
            title=f'Words added'
        ).add_description(
            f"""Words that were added to the database:
            {', '.join(words_from_message)}"""
        )
        await message.channel.send(embed=add_words_embed)
        bot_logger.info('Message for adding words sent')
    else:
        await permission_abuse(message)

    return


async def handle_remove_word_command(message: discord.Message):
    """Handle the command to remove a word from the database.

    This function removes a word from the database if the user has admin permission,
    otherwise, it sends a message indicating the lack of permission.

    Parameters:
        message (discord.Message): The message containing the command.
    """
    bot_logger.debug('Removing word from database')

    # check if user has permission
    user_id = message.author.id
    if sql_statements.check_user_is_admin(user_id):
        # get word and remove word
        remove_word = message.content.lower().split(' ')[1]
        sql_statements.remove_word(remove_word)

        # create embed
        remove_word_embed = embed.Embed(
            client.user.avatar,
            title=f'Removed word'
        ).add_description(
            f"""Removed word from database:
            {remove_word}"""
        )
        await message.channel.send(embed=remove_word_embed)
        bot_logger.info('Message for removing word sent')
    else:
        await permission_abuse(message)

    return


async def handle_word_count(message: discord.Message, word: str):
    """Handle word count in a message.

    This function counts the occurrences of a specific word in a message,
    updates the count in the database, and sends a message indicating the first occurrence
    of the word by the user, if applicable.

    Parameters:
        message (discord.Message): The message containing the word.
        word (str): The word to count in the message.
    """
    bot_logger.debug(f'Word: {word} found in message')
    word_count = message.content.lower().count(word)
    user_id = message.author.id

    if sql_statements.get_count(user_id, word) is None:
        bot_logger.debug(f'First time {user_id} has said {word}')
        sql_statements.update_user_count(user_id, word, word_count)

        username = await client.fetch_user(user_id)

        # Create embed
        first_time_embed = embed.Embed(
            client.user.avatar,
            title=f'First time :smirk:'
        ).add_description(
            f"""{username} was a naughty boy and said {word}\n
            His first time... :sweat_drops:"""
        )
        await message.channel.send(embed=first_time_embed)
        bot_logger.info(f'First time message sent: {username}, {word}')
        return

    sql_statements.update_user_count(user_id, word, word_count)


async def permission_abuse(message: discord.Message):
    """Send mod abuse message

        Parameters:
            message (discord.Message): Message needed for sending mod message.
    """
    bot_logger.debug('Permission abuse')
    mod_abuse_embed = embed.Embed(
        client.user.avatar,
        title=f'No permission'
    ).add_description(
        f"""You have no permission to remove the word\n
        Call the admin: {await client.fetch_user(admin_id)}"""
    )
    await message.channel.send(embed=mod_abuse_embed)
    bot_logger.info('Message for mod abuser sent')

client.run(token, log_handler=None)
