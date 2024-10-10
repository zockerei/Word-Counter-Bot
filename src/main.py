# Tested with python 3.11
import discord
from discord import app_commands
import logging.config
import yaml
from config import LOGGING_CONFIG_PATH, BOT_CONFIG_PATH, LOG_FILE_PATH
import sql
import embed

# Logging setup
with open(LOGGING_CONFIG_PATH, 'r') as config_file:
    logging_config = yaml.safe_load(config_file)
    logging_config['handlers']['file']['filename'] = str(LOG_FILE_PATH)
    logging.config.dictConfig(logging_config)

discord_logger = logging.getLogger('discord')
bot_logger = logging.getLogger('bot.main')
bot_logger.info('Logging setup complete')

# Initialize SQL statements with the correct database path
sql_statements = sql.SqlStatements()

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Load bot configuration
with open(BOT_CONFIG_PATH, 'r') as config_file:
    bot_config = yaml.safe_load(config_file)
    token, words, server_id, channel_id, admin_ids = (
        bot_config['token'],
        bot_config['words'],
        bot_config['server_id'],
        bot_config['channel_id'],
        bot_config['admin_ids']
    )
bot_logger.debug(f'{token} | {words} | {server_id} | {channel_id} | {admin_ids}')
bot_logger.info('bot_config loaded')

class MyClient(discord.Client):
    """
    Custom Discord client class that sets up the command tree.
    """

    def __init__(self):
        """
        Initialize the custom client with intents and command tree.
        """
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        """
        Set up the bot by syncing the command tree with the specified guild.
        """
        await self.tree.sync(guild=discord.Object(id=server_id))

client = MyClient()

@client.event
async def on_ready():
    """
    Handle the event when the bot is ready.

    This function logs in, sets up the database, adds words to the database,
    retrieves server member IDs and adds them to the database, and adds admin users.
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
    sql_statements.add_admins(*admin_ids)
    bot_logger.info('Bot ready')

@client.event
async def on_member_join(member: discord.Member):
    """
    Handle the event when a new member joins the server.

    Args:
        member (discord.Member): The member who joined the server.
    """
    bot_logger.debug(f'{member} joined')

    # create new user in database
    sql_statements.add_user_ids(member.id)

    # create embed for new user
    username = member.display_name 
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

@client.tree.command(name="c", description="Count occurrences of a word for a specific user")
@app_commands.describe(word="The word to count", user="The user to check")
async def count(interaction: discord.Interaction, word: str, user: discord.Member):
    """
    Count occurrences of a word for a specific user.

    Args:
        interaction (discord.Interaction): The interaction object.
        word (str): The word to count.
        user (discord.Member): The user to check.
    """
    await interaction.response.defer()
    bot_logger.debug('Get count of user with word')

    converted_user_id = user.id
    count_user_id = sql_statements.get_count(converted_user_id, word)
    username = user.display_name 

    if count_user_id is None:
        zero_count_embed = embed.Embed(
            client.user.avatar,
            title=f'{username} is clean'
        ).add_description(
            f"""{username} has said {word} 0 times\n
            (Or he tricked the system)"""
        )
        await interaction.followup.send(embed=zero_count_embed)
        return

    count_embed = embed.Embed(
        client.user.avatar,
        title=f'Count from {username}'
    ).add_description(
        f'{username} has said {word} {count_user_id} times'
    )

    highest_count_tuple = sql_statements.get_highest_count_column(word)
    highest_count_user = client.get_user(highest_count_tuple[0]).display_name 
    count_embed.add_footer(
        f'The person who has said {word} the most is '
        f'{highest_count_user} with {highest_count_tuple[2]} times'
    )
    await interaction.followup.send(embed=count_embed)
    bot_logger.debug('Count message sent')

@client.tree.command(name="hc", description="Retrieve the highest count of a word")
@app_commands.describe(word="The word to check")
async def highest_count(interaction: discord.Interaction, word: str):
    """
    Retrieve the highest count of a word across all users.

    Args:
        interaction (discord.Interaction): The interaction object.
        word (str): The word to check.
    """
    await interaction.response.defer()
    bot_logger.debug('Get highest count of user from word')
    highest_count_tuple = sql_statements.get_highest_count_column(word)

    if highest_count_tuple is None:
        no_count_embed = embed.Embed(
            client.user.avatar,
            title=f'Dead Server'
        ).add_description(
            f"""No User in this Server has said {word}\n
            Or the word is not being monitored :eyes:"""
        )
        await interaction.followup.send(embed=no_count_embed)
        return

    highest_count_embed = embed.Embed(
        client.user.avatar,
        title=f'Highest count from all Users'
    )
    username = client.get_user(highest_count_tuple[0]).display_name 
    highest_count_embed.add_description(
        f"""The user who has said {word} the most is ||{username}||\n
        With an impressive amount of {highest_count_tuple[2]} times"""
    )
    await interaction.followup.send(embed=highest_count_embed)
    bot_logger.info('Highest count message sent')

@client.tree.command(name="thc", description="Retrieve the total highest count of all words")
async def total_highest_count(interaction: discord.Interaction):
    """
    Retrieve the total highest count of all words across all users.

    Args:
        interaction (discord.Interaction): The interaction object.
    """
    await interaction.response.defer()
    bot_logger.debug('Get user with highest amount of all words')
    total_highest_count = sql_statements.get_total_highest_count_column()

    if total_highest_count is None:
        no_count_embed = embed.Embed(
            client.user.avatar,
            title=f'Dead Server'
        ).add_description(
            f"""No User in this Server has said any word...\n
            Or they tricked the system (not hard)"""
        )
        await interaction.followup.send(embed=no_count_embed)
        return

    username = client.get_user(total_highest_count[0]).display_name 
    thc_embed = embed.Embed(
        client.user.avatar,
        title=f'Highest count of all words'
    ).add_description(
        f"""The winner for the Highest count of all words is... ||{username}!||\n
        Who has said {total_highest_count[1]} {total_highest_count[2]} times"""
    ).add_footer(
        f'Imagine'
    )
    await interaction.followup.send(embed=thc_embed)
    bot_logger.info('Message for total highest count sent')

@client.tree.command(name="sw", description="Show all tracked words")
async def show_words(interaction: discord.Interaction):
    """
    Show all tracked words in the database.

    Args:
        interaction (discord.Interaction): The interaction object.
    """
    await interaction.response.defer()
    bot_logger.debug('Show all words from database')
    words_database = sql_statements.get_words()

    words_embed = embed.Embed(
        client.user.avatar,
        title=f'All words'
    ).add_description(
        f"""Here is a list of all the words you should rather not say...\n
        {', '.join(words_database)}"""
    )
    await interaction.followup.send(embed=words_embed)
    bot_logger.info('Message for all words sent')

@client.tree.command(name="add_word", description="Add word to database (admin-only)")
@app_commands.describe(word="The word to add")
async def add_word(interaction: discord.Interaction, word: str):
    """
    Add a word to the database (admin-only).

    Args:
        interaction (discord.Interaction): The interaction object.
        word (str): The word to add to the database.
    """
    await interaction.response.defer()
    bot_logger.debug('Add word to database')

    if sql_statements.check_user_is_admin(interaction.user.id):
        sql_statements.add_words(word)

        add_word_embed = embed.Embed(
            client.user.avatar,
            title=f'Word added'
        ).add_description(
            f"""Word that was added to the database:
            {word}"""
        )
        await interaction.followup.send(embed=add_word_embed)
        bot_logger.info('Message for adding word sent')
    else:
        await permission_abuse(interaction)

@client.tree.command(name="rw", description="Remove a word from database (admin-only)")
@app_commands.describe(word="The word to remove")
async def remove_word(interaction: discord.Interaction, word: str):
    """
    Remove a word from the database (admin-only).

    Args:
        interaction (discord.Interaction): The interaction object.
        word (str): The word to remove from the database.
    """
    await interaction.response.defer()
    bot_logger.debug('Removing word from database')

    if sql_statements.check_user_is_admin(interaction.user.id):
        sql_statements.remove_word(word)

        remove_word_embed = embed.Embed(
            client.user.avatar,
            title=f'Removed word'
        ).add_description(
            f"""Removed word from database:
            {word}"""
        )
        await interaction.followup.send(embed=remove_word_embed)
        bot_logger.info('Message for removing word sent')
    else:
        await permission_abuse(interaction)

@client.tree.command(name="help", description="Show bot usage instructions")
async def help_command(interaction: discord.Interaction):
    """
    Show bot usage instructions.

    Args:
        interaction (discord.Interaction): The interaction object.
    """
    await interaction.response.defer()
    bot_logger.debug('Handling help command')
    help_embed = embed.Embed(
        client.user.avatar,
        title='Word Counter Bot Help'
    ).add_description(
        """Here are the available commands:
        
        /count [word] [user]: Count occurrences of a word for a specific user.
        /highest_count [word]: Retrieve the highest count of a word.
        /total_highest_count: Retrieve the total highest count of all words.
        /show_words: Show all tracked words.
        /add_word [word]: Add word to database (admin-only).
        /remove_word [word]: Remove a word from database (admin-only).
        """
    ).add_footer(
        "Use these commands wisely!"
    )
    
    await interaction.followup.send(embed=help_embed)
    bot_logger.info('Help message sent')

async def handle_word_count(message: discord.Message, word: str):
    """
    Handle word count in a message.

    This function updates the count for a word said by a user and sends a notification
    if it's the first time the user has said the word.

    Args:
        message (discord.Message): The message containing the word.
        word (str): The word to count in the message.
    """
    bot_logger.debug(f'Word: {word} found in message')
    word_count = message.content.lower().count(word)
    user_id = message.author.id

    if sql_statements.get_count(user_id, word) is None:
        bot_logger.debug(f'First time {user_id} has said {word}')
        sql_statements.update_user_count(user_id, word, word_count)

        username = message.author.display_name 

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

async def permission_abuse(interaction: discord.Interaction):
    """
    Send a mod abuse message when a user without permissions attempts an admin action.

    Args:
        interaction (discord.Interaction): The interaction object.
    """
    bot_logger.debug('Permission abuse')
    admin_user = client.get_user(admin_ids[0]).display_name
    mod_abuse_embed = embed.Embed(
        client.user.avatar,
        title=f'No permission'
    ).add_description(
        f"""You have no permission to perform this action\n
        Call the admin: {admin_user}"""
    )
    await interaction.followup.send(embed=mod_abuse_embed)
    bot_logger.info('Message for mod abuser sent')

client.run(token, log_handler=None)