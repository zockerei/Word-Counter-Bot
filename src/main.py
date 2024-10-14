# Tested with python 3.11
import discord
from discord import app_commands
import logging.config
import yaml
from config import LOGGING_CONFIG_PATH, BOT_CONFIG_PATH, LOG_FILE_PATH
import sql
from discord import Embed, Color
from collections import defaultdict

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
bot_logger.debug(f'Intents setup complete: {intents}')

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
        # Sync commands with a specific guild (server)
        guild = discord.Object(id=server_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        bot_logger.info('Command tree synced with specific guild')

    async def scan_server_history(self):
        """
        Scan the server's message history for words in the database.
        Update the counts if higher than what's stored in the database.
        """
        bot_logger.info("Starting server history scan")
        guild = self.get_guild(server_id)
        words_list = sql_statements.get_words()
        
        total_messages = 0
        total_channels = len(guild.text_channels)
        word_counts = defaultdict(lambda: defaultdict(int))
        
        for channel_index, channel in enumerate(guild.text_channels, 1):
            try:
                channel_messages = await self.scan_channel(channel, words_list, word_counts)
                total_messages += channel_messages
                bot_logger.debug(f"Completed channel {channel.name} ({channel_index}/{total_channels}): {channel_messages} messages")
                
                # Scan threads in the channel
                threads = []
                async for thread in channel.archived_threads():
                    threads.append(thread)
                threads.extend(channel.threads)
                
                for thread_index, thread in enumerate(threads, 1):
                    thread_messages = await self.scan_channel(thread, words_list, word_counts)
                    total_messages += thread_messages
                    bot_logger.debug(f"Completed thread {thread.name} in {channel.name} ({thread_index}/{len(threads)}): {thread_messages} messages")
            except discord.errors.Forbidden:
                bot_logger.warning(f"No access to channel {channel.name}")

        # Update database with accumulated counts
        for user_id, user_words in word_counts.items():
            for word, count in user_words.items():
                current_count = sql_statements.get_count(user_id, word) or 0
                if count > current_count:
                    sql_statements.update_user_count(user_id, word, count)
                    bot_logger.debug(f"Updated count for user {user_id}, word '{word}': {current_count} -> {count}")

        bot_logger.info(f"Server history scan completed. Total messages processed: {total_messages}")

    async def scan_channel(self, channel, word_list, word_counts):
        """
        Scan a single channel or thread for messages.
        """
        message_count = 0
        last_message_id = None
        
        while True:
            try:
                messages = []
                async for message in channel.history(limit=100, before=last_message_id and discord.Object(id=last_message_id)):
                    messages.append(message)
                    self.process_message_history(message, word_list, word_counts)
                    message_count += 1

                if not messages:
                    break
                
                last_message_id = messages[-1].id
                
                bot_logger.debug(f"Processed {message_count} messages in {channel.name}")
            except discord.errors.HTTPException as e:
                bot_logger.error(f"Error fetching messages from {channel.name}: {e}")
                break

        return message_count

    async def scan_user_history(self, user_id):
        """
        Scan the server's message history for a specific user.
        """
        bot_logger.info(f"Starting history scan for user {user_id}")
        guild = self.get_guild(server_id)
        words_list = sql_statements.get_words()
        word_counts = defaultdict(int)
        
        total_messages = 0
        total_channels = len(guild.text_channels)
        
        for channel_index, channel in enumerate(guild.text_channels, 1):
            try:
                channel_messages = 0
                async for message in channel.history(limit=None):
                    if message.author.id == user_id:
                        self.process_message_history(message, words_list, {user_id: word_counts})
                        channel_messages += 1
                        total_messages += 1
                
                bot_logger.debug(f"Processed {channel_messages} messages from user {user_id} in channel {channel.name} ({channel_index}/{total_channels})")
                
                # Scan threads in the channel
                threads = []
                async for thread in channel.archived_threads():
                    threads.append(thread)
                threads.extend(channel.threads)
                
                for thread_index, thread in enumerate(threads, 1):
                    thread_messages = 0
                    async for message in thread.history(limit=None):
                        if message.author.id == user_id:
                            self.process_message_history(message, words_list, {user_id: word_counts})
                            thread_messages += 1
                            total_messages += 1
                    
                    bot_logger.debug(f"Processed {thread_messages} messages from user {user_id} in thread {thread.name} ({thread_index}/{len(threads)}) of channel {channel.name}")
            except discord.errors.Forbidden:
                bot_logger.warning(f"No access to channel {channel.name}")

        # Update database with accumulated counts
        for word, count in word_counts.items():
            current_count = sql_statements.get_count(user_id, word) or 0
            if count > current_count:
                sql_statements.update_user_count(user_id, word, count)
                bot_logger.debug(f"Updated count for user {user_id}, word '{word}': {current_count} -> {count}")

        bot_logger.info(f"User history scan completed for user {user_id}. Total messages processed: {total_messages}")

    async def scan_for_new_word(self, new_word):
        """
        Scan the server's message history for a newly added word.
        """
        bot_logger.info(f"Starting server scan for new word '{new_word}'")
        guild = self.get_guild(server_id)
        word_counts = defaultdict(int)
        
        total_messages = 0
        total_channels = len(guild.text_channels)
        
        for channel_index, channel in enumerate(guild.text_channels, 1):
            try:
                channel_messages = 0
                async for message in channel.history(limit=None):
                    if new_word.lower() in message.content.lower():
                        word_occurrence = message.content.lower().count(new_word.lower())
                        word_counts[message.author.id] += word_occurrence
                        channel_messages += 1
                        total_messages += 1
                
                bot_logger.debug(f"Processed {channel_messages} messages in channel {channel.name} ({channel_index}/{total_channels}) for new word '{new_word}'")
                
                # Scan threads in the channel
                threads = []
                async for thread in channel.archived_threads():
                    threads.append(thread)
                threads.extend(channel.threads)
                
                for thread_index, thread in enumerate(threads, 1):
                    thread_messages = 0
                    async for message in thread.history(limit=None):
                        if new_word.lower() in message.content.lower():
                            word_occurrence = message.content.lower().count(new_word.lower())
                            word_counts[message.author.id] += word_occurrence
                            thread_messages += 1
                            total_messages += 1
                    
                    bot_logger.debug(f"Processed {thread_messages} messages in thread {thread.name} ({thread_index}/{len(threads)}) of channel {channel.name} for new word '{new_word}'")
            except discord.errors.Forbidden:
                bot_logger.warning(f"No access to channel {channel.name}")

        # Update database with accumulated counts, only if the new count is higher
        for user_id, count in word_counts.items():
            current_count = sql_statements.get_count(user_id, new_word) or 0
            if count > current_count:
                sql_statements.update_user_count(user_id, new_word, count)
                bot_logger.debug(f"Updated count for user {user_id}, new word '{new_word}': {current_count} -> {count}")
            else:
                bot_logger.debug(f"No update needed for user {user_id}, new word '{new_word}': current count {current_count} >= new count {count}")

        bot_logger.info(f"Server scan completed for new word '{new_word}'. Total messages processed: {total_messages}")
        
    @staticmethod
    def process_message_history(message, word_list, word_counts):
        """
        Process a single message from the history.
        """
        for word in word_list:
            if word.lower() in message.content.lower():
                word_occurrence = message.content.lower().count(word.lower())
                word_counts[message.author.id][word] += word_occurrence

client = MyClient()

@client.event
async def on_ready():
    """
    Handle the event when the bot is ready.
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

    # Scan server history
    await client.scan_server_history()

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

    # Scan user's history
    await client.scan_user_history(member.id)

    # create embed for new user
    username = member.display_name 
    new_user_embed = Embed(
        title='A new victim',
        description=f"""A new victim joined the Server\n
        Be aware of what you type {username}... 😳""",
        color=Color.blue()
    ).set_footer(
        text=', '.join(sql_statements.get_words())
    )

    # send embed to the designated channel
    await client.get_channel(channel_id).send(embed=new_user_embed)
    bot_logger.info('New user message sent')

@client.event
async def on_message(message: discord.Message):
    """
    Handles the event when a message is received.

    Args:
        message (discord.Message): The message received by the bot.
    """
    bot_logger.debug('Message received')
    if message.author == client.user:
        return

    current_words = sql_statements.get_words()
    words_in_message = message.content.lower().split()
    for word in current_words:
        if word.lower() in words_in_message:
            await handle_word_count(message, word)
            bot_logger.debug(f'Word "{word}" found in message')
        else:
            bot_logger.debug(f'Word "{word}" not found in message')

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
        zero_count_embed = Embed(
            title=f'{username} is clean',
            description=f"""{username} has said {word} 0 times\n
            (Or he tricked the system)""",
            color=Color.green()
        )
        await interaction.followup.send(embed=zero_count_embed)
        return

    count_embed = Embed(
        title=f'Count from {username}',
        description=f'{username} has said {word} {count_user_id} times',
        color=Color.blue()
    )

    highest_count_tuple = sql_statements.get_highest_count_column(word)
    highest_count_user = client.get_user(highest_count_tuple[0]).display_name 
    count_embed.set_footer(text=f'The person who has said {word} the most is '
                                f'{highest_count_user} with {highest_count_tuple[2]} times\n'
                                f'Imagine 🐕 💦')
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
        no_count_embed = Embed(
            title='Dead Server',
            description=f"""No User in this Server has said {word}\n
            Or the word is not being monitored :eyes:""",
            color=Color.red()
        )
        await interaction.followup.send(embed=no_count_embed)
        return

    username = client.get_user(highest_count_tuple[0]).display_name
    highest_count_embed = Embed(
        title='Highest count from all Users',
        description=f"""The user who has said {word} the most is {username}\n
        With an impressive amount of {highest_count_tuple[2]} times""",
        color=Color.gold()
    )
    await interaction.followup.send(embed=highest_count_embed)
    bot_logger.info('Highest count message sent')

@client.tree.command(name="thc", description="Retrieve the total highest count of all words")
async def total_highest_count_command(interaction: discord.Interaction):
    """
    Retrieve the total highest count of all words across all users.

    Args:
        interaction (discord.Interaction): The interaction object.
    """
    await interaction.response.defer()
    bot_logger.debug('Get user with highest amount of all words')
    highest_count_result = sql_statements.get_total_highest_count_column()

    if highest_count_result is None:
        no_count_embed = Embed(
            title='Dead Server',
            description=f"""No User in this Server has said any word...\n
            Or they tricked the system (not hard)""",
            color=Color.red()
        )
        await interaction.followup.send(embed=no_count_embed)
        return

    username = client.get_user(highest_count_result[0]).display_name 
    thc_embed = Embed(
        title='Highest count of all words',
        description=f"""The winner for the Highest count of all words is... {username}!\n
        Who has said {highest_count_result[1]} {highest_count_result[2]} times""",
        color=Color.gold()
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

    words_embed = Embed(
        title='All words',
        description=f"""Here is a list of all the words you should rather not say...\n
        {', '.join(words_database)}""",
        color=Color.blue()
    )
    await interaction.followup.send(embed=words_embed)
    bot_logger.info('Message for all words sent')

@client.tree.command(name="aw", description="Add word to database (admin-only)")
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

        # Scan server for new word
        await client.scan_for_new_word(word)

        add_word_embed = Embed(
            title='Word added',
            description=f"""Word that was added to the database:
            {word}""",
            color=Color.green()
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

        remove_word_embed = Embed(
            title='Removed word',
            description=f"""Removed word from database:
            {word}""",
            color=Color.red()
        )
        await interaction.followup.send(embed=remove_word_embed)
        bot_logger.info('Message for removing word sent')
    else:
        await permission_abuse(interaction)

@client.tree.command(name="h", description="Show bot usage instructions")
async def help_command(interaction: discord.Interaction):
    """
    Show bot usage instructions.

    Args:
        interaction (discord.Interaction): The interaction object.
    """
    await interaction.response.defer()
    bot_logger.debug('Handling help command')
    help_embed = Embed(
        title='Word Counter Bot Help',
        description="""Here are the available commands:
        
        /c [word] [user]: Count occurrences of a word for a specific user.
        /hc [word]: Retrieve the highest count of a word.
        /thc: Retrieve the total highest count of all words.
        /sw: Show all tracked words.
        /aw [word]: Add word to database (admin-only).
        /rw [word]: Remove a word from database (admin-only).
        """,
        color=Color.blue()
    ).set_footer(
        text="Use these commands wisely!"
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
    word_count = message.content.lower().split().count(word.lower())
    user_id = message.author.id

    if sql_statements.get_count(user_id, word) is None:
        bot_logger.debug(f'First time {user_id} has said {word}')
        sql_statements.update_user_count(user_id, word, word_count)

        username = message.author.display_name 

        first_time_embed = Embed(
            title='First time 😩',
            description=f"""{username} was a naughty boy and said {word}\n
            His first time... 💦""",
            color=Color.red()
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
    mod_abuse_embed = Embed(
        title='No permission',
        description=f"""You have no permission to perform this action\n
        Call the admin: {admin_user}""",
        color=Color.red()
    )
    await interaction.followup.send(embed=mod_abuse_embed)
    bot_logger.info('Message for mod abuser sent')

client.run(token, log_handler=None)