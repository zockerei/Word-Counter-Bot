from discord.ext import commands
from discord import Color, Embed
from unidecode import unidecode
import db.queries as queries
import logging
import discord
from logic import scan
import re

events_logger = logging.getLogger('cogs.events')


class Events(commands.Cog):
    """
    A cog that handles various Discord events and bot interactions.

    This cog manages events such as bot startup, member joins, and message monitoring.
    It also handles word tracking and user management functionality.

    Attributes:
        bot: The Discord bot instance
        config: The bot configuration settings
    """
    def __init__(self, bot):
        """
        Initialize the Events cog.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot
        events_logger.info('Events cog initialized')

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Handle the bot's ready event.

        Performs initialization tasks when the bot starts up:
        - Syncs command tree with the guild
        - Initializes word list and user IDs
        - Performs initial message scan if enabled
        """
        guild = discord.Object(id=self.bot.config.server_id)
        self.bot.tree.copy_global_to(guild=guild)
        await self.bot.tree.sync(guild=guild)
        events_logger.info('Command tree synced with specific guild')

        queries.add_words(*self.bot.config.words)
        queries.add_user_ids(*[member.id for member in self.bot.get_guild(self.bot.config.server_id).members])
        queries.add_admins(*self.bot.config.admin_ids)
        events_logger.info(
            f'Initialized with {len(self.bot.config.words)} words and {len(self.bot.config.admin_ids)} admins'
        )

        if not self.bot.config.disable_initial_scan:
            await scan(self.bot, self.bot.config.server_id)
            events_logger.info('Initial scan completed')

        events_logger.info('Bot ready')

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        Handle the event when a new member joins the server.

        Args:
            member (discord.Member): The member who joined the server.
        """
        events_logger.info(f"Member joined - Name: {member.display_name}, ID: {member.id}")
        queries.add_user_ids(member.id)

        username = member.display_name
        new_user_embed = Embed(
            title='A new victim',
            description=f"""A new victim joined the Server\n
            Be aware of what you type {username}... 😳""",
            color=Color.blue()
        ).set_footer(
            text=', '.join(queries.get_words())
        )

        await self.bot.get_channel(self.bot.config.channel_id).send(embed=new_user_embed)

        await scan(self.bot, self.bot.config.server_id, target_user_id=member.id)
        events_logger.info('New user message sent')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Handles the event when a message is received.

        Args:
            message (discord.Message): The message received by the bot.
        """
        events_logger.debug('Message received')
        if message.author == self.bot.user:
            return

        formatted_content = unidecode(message.content).lower()
        events_logger.debug(f'Processing message from {message.author.display_name} (ID: {message.author.id})')

        current_words = queries.get_words()
        for word in current_words:
            if word:
                pattern = r'\b' + re.escape(word) + r'\b'
                matches = re.findall(pattern, formatted_content)
                if matches:
                    await self.handle_word_count(message, word, matches)
                    events_logger.info(f'Tracked word "{word}" found in message from {message.author.display_name}')
                else:
                    events_logger.debug(f'Word: "{word}" not found in message')

    async def handle_word_count(self, message: discord.Message, word: str, matches: list):
        """
        Handle word count in a message.

        This function updates the count for a word said by a user and sends a notification
        if it's the first time the user has said the word.

        Args:
            message (discord.Message): The message containing the word.
            word (str): The word to count in the message.
            matches (list): The list of matches found in the message.
        """
        events_logger.debug(f'Word: {word} found in message')

        word_count = len(matches)
        user_id = message.author.id

        if queries.get_count(user_id, word) is None:
            events_logger.debug(f'First time {user_id} has said {word}')
            queries.update_user_count(user_id, word, word_count)

            username = message.author.display_name

            first_time_embed = Embed(
                title='First time 😩',
                description=f"""{username} was a naughty boy and said {word}\n
                His first time... 💦""",
                color=Color.red()
            )
            await message.channel.send(embed=first_time_embed)
            events_logger.info(f'First time message sent: {username}, {word}')
            return

        queries.update_user_count(user_id, word, word_count)


async def setup(bot):
    """
    Set up the Events cog.

    Args:
        bot: The Discord bot instance to add this cog to
    """
    await bot.add_cog(Events(bot))
    events_logger.info('Events cog loaded')
