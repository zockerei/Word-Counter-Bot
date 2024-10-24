import discord
from discord import app_commands, Embed, Color
import logging.config
from config.config import setup_logging, load_bot_config
import sql
from collections import defaultdict
from unidecode import unidecode

setup_logging()
bot_logger = logging.getLogger('bot.main')
bot_logger.info('Logging setup complete')

token, words, server_id, channel_id, admin_ids, disable_initial_scan = load_bot_config()

# Initialize SQL
sql_statements = sql.SqlStatements()

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot_logger.info('Intents setup complete')

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
        # Sync commands with a specific guild (server_id)
        guild = discord.Object(id=server_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        bot_logger.info('Command tree synced with specific guild')

    async def scan(self, word_counts=None, target_user_id=None, target_word=None):
        """
        General scan method for server, user, or word.

        Args:
            word_counts (dict, optional): A dictionary to accumulate word counts.
            target_user_id (int, optional): If provided, scans only for this user.
            target_word (str, optional): If provided, scans for this word only.
        """
        bot_logger.info(f"Starting scan. User: {target_user_id}, Word: {target_word}")
        guild = self.get_guild(server_id)
        word_counts = word_counts or defaultdict(lambda: defaultdict(int))
        total_messages_scanned = 0

        for channel in guild.text_channels:
            messages_scanned = await self.scan_channel(channel, word_counts, target_user_id, target_word)
            total_messages_scanned += messages_scanned

        self.update_word_counts(word_counts)
        bot_logger.info(f"Scan completed. Total messages scanned: {total_messages_scanned}")

    async def scan_channel(self, channel, word_counts, target_user_id=None, target_word=None):
        """
        Scans a channel and its threads.

        Args:
            channel (discord.TextChannel): The channel to scan.
            word_counts (dict): A dictionary to accumulate word counts.
            target_user_id (int, optional): If provided, scans only for this user.
            target_word (str, optional): If provided, scans for this word only.

        Returns:
            int: The number of messages scanned.
        """
        # Scan messages in the channel
        messages_scanned = await self.scan_messages(channel, word_counts, target_user_id, target_word)

        # Scan messages in the channel's threads
        threads = [thread async for thread in channel.archived_threads()] + channel.threads
        for thread in threads:
            messages_scanned += await self.scan_messages(thread, word_counts, target_user_id, target_word)

        return messages_scanned

    async def scan_messages(self, channel, word_counts, target_user_id=None, target_word=None):
        """
        Scans messages in a channel or thread.

        Args:
            channel (discord.TextChannel or discord.Thread): The channel or thread to scan.
            word_counts (dict): A dictionary to accumulate word counts.
            target_user_id (int, optional): If provided, scans only for this user.
            target_word (str, optional): If provided, scans for this word only.

        Returns:
            int: The number of messages scanned.
        """
        messages_scanned = 0
        async for message in channel.history(limit=None):
            messages_scanned += 1
            if target_user_id and message.author.id != target_user_id:
                continue
            self.process_message(message, word_counts, target_word)
        return messages_scanned

    @staticmethod
    def process_message(message, word_counts, target_word=None):
        """
        Processes a message to count occurrences of words.

        Args:
            message (discord.Message): The message to process.
            word_counts (dict): A dictionary to accumulate word counts.
            target_word (str, optional): If provided, counts only occurrences of this word.
        """
        # Use unidecode to convert styled text to ASCII
        content_normalized = unidecode(message.content).lower()
        
        words_to_check = [target_word] if target_word else sql_statements.get_words()

        for word in words_to_check:
            if word and word in content_normalized:
                word_counts[message.author.id][word] += content_normalized.count(word)

    @staticmethod
    def update_word_counts(word_counts):
        """
        Updates the database with word counts, only if the new count is higher.

        Args:
            word_counts (dict): A dictionary containing word counts for users.
        """
        for user_id, update_words in word_counts.items():
            for word, update_count in update_words.items():
                current_count = sql_statements.get_count(user_id, word)
                if current_count is None:
                    sql_statements.add_user_has_word(user_id, word, update_count)
                elif update_count > current_count:
                    sql_statements.update_user_count(user_id, word, update_count - current_count)

client = MyClient()

@client.event
async def on_ready():
    sql_statements.create_tables()
    sql_statements.add_words(*words)
    sql_statements.add_user_ids(*[member.id for member in client.get_guild(server_id).members])
    sql_statements.add_admins(*admin_ids)

    if not disable_initial_scan:
        await client.scan()
    bot_logger.info('Bot ready')

@client.event
async def on_member_join(member: discord.Member):
    """
    Handle the event when a new member joins the server.

    Args:
        member (discord.Member): The member who joined the server.
    """
    bot_logger.info(f"{member} joined")
    bot_logger.debug(f'Member ID: {member.id}')
    sql_statements.add_user_ids(member.id)

    username = member.display_name 
    new_user_embed = Embed(
        title='A new victim',
        description=f"""A new victim joined the Server\n
        Be aware of what you type {username}... 😳""",
        color=Color.blue()
    ).set_footer(
        text=', '.join(sql_statements.get_words())
    )

    await client.get_channel(channel_id).send(embed=new_user_embed)

    await client.scan(target_user_id=member.id)
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

    # Format the message content using unidecode
    formatted_content = unidecode(message.content).lower()
    bot_logger.debug(f'Formatted content: {formatted_content}')

    current_words = sql_statements.get_words()
    words_in_message = formatted_content.split()
    for word in current_words:
        if word.lower() in words_in_message:
            await handle_word_count(message, word)
            bot_logger.info(f'Word: "{word}" found in message')
        else:
            bot_logger.debug(f'Word: "{word}" not found in message')

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
    bot_logger.debug(f'Get count of user: {user.display_name} with word: {word}')

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
    bot_logger.info('Count message sent')

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
    bot_logger.debug(f'Get highest count of user from word: {word}')
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

    bot_logger.debug(f'Username: {highest_count_tuple[0]}')
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

    bot_logger.debug(f'Username: {highest_count_result[0]}')
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
    bot_logger.debug(f'Add word: {word} to database')

    if sql_statements.check_user_is_admin(interaction.user.id):
        sql_statements.add_words(word)
        await client.scan(target_word=word)
        bot_logger.info(f"Word '{word}' added and scanned")

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
    bot_logger.debug(f'Removing word: {word} from database')

    if sql_statements.check_user_is_admin(interaction.user.id):
        sql_statements.remove_word(word)
        bot_logger.debug(f'Word: {word} removed from database')

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
        /uwc [user]: Show all words and their counts for a specific user.
        """,
        color=Color.blue()
    ).set_footer(
        text="Use these commands wisely!"
    )
    
    await interaction.followup.send(embed=help_embed)
    bot_logger.info('Help message sent')

@client.tree.command(name="uwc", description="Show all words and their counts for a specific user")
@app_commands.describe(member="The user to check")
async def user_word_counts(interaction: discord.Interaction, member: discord.Member):
    """
    Show all words and their counts for a specific user.

    Args:
        interaction (discord.Interaction): The interaction object.
        member (discord.Member): The user to check.
    """
    await interaction.response.defer()
    bot_logger.debug(f'Get all words and counts for user: {member.id}')

    user_id = member.id
    word_counts = sql_statements.get_user_word_counts(user_id)

    if not word_counts:
        no_words_embed = Embed(
            title=f'{member.display_name} has no words',
            description=f"{member.display_name} hasn't said any tracked words.",
            color=Color.red()
        )
        await interaction.followup.send(embed=no_words_embed)
        return

    sorted_word_counts = sorted(word_counts, key=lambda x: x[1], reverse=True)
    words_description = "\n".join([f"{word}: {user_count}" for word, user_count in sorted_word_counts])
    user_words_embed = Embed(
        title=f'Word counts for {member.display_name}',
        description=words_description,
        color=Color.blue()
    )
    await interaction.followup.send(embed=user_words_embed)
    bot_logger.info(f'Word counts sent')

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

    # Use the same formatting as in on_message
    formatted_content = unidecode(message.content).lower()

    word_count = formatted_content.split().count(word.lower())
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
    admin_users = [client.get_user(admin_id).display_name for admin_id in admin_ids]
    admin_list = ', '.join(admin_users)
    mod_abuse_embed = Embed(
        title='No permission',
        description=f"""You have no permission to perform this action\n
        Call the admins: {admin_list}""",
        color=Color.red()
    )
    await interaction.followup.send(embed=mod_abuse_embed)
    bot_logger.info('Message for mod abuser sent')

client.run(token, log_handler=None)
