from discord.ext import commands
import db.queries as queries
from discord import Color, Embed
from unidecode import unidecode
import logging
import discord

events_logger = logging.getLogger('cogs.events')

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Sync commands with a specific guild (server_id)
        guild = discord.Object(id=server_id)
        self.bot.tree.copy_global_to(guild=guild)
        await self.bot.tree.sync(guild=guild)
        events_logger.info('Command tree synced with specific guild')

        queries.create_tables()
        queries.add_words(*words)
        queries.add_user_ids(*[member.id for member in self.bot.get_guild(server_id).members])
        queries.add_admins(*admin_ids)

        if not disable_initial_scan:
            await self.bot.scan()
        events_logger.info('Bot ready')

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        Handle the event when a new member joins the server.

        Args:
            member (discord.Member): The member who joined the server.
        """
        events_logger.info(f"{member} joined")
        events_logger.debug(f'Member ID: {member.id}')
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

        await self.bot.get_channel(channel_id).send(embed=new_user_embed)

        await self.bot.scan(target_user_id=member.id)
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

        # Format the message content using unidecode
        formatted_content = unidecode(message.content).lower()
        events_logger.debug(f'Formatted content: {formatted_content}')

        current_words = queries.get_words()
        words_in_message = formatted_content.split()
        for word in current_words:
            if word.lower() in words_in_message:
                await self.handle_word_count(message, word)
                events_logger.info(f'Word: "{word}" found in message')
            else:
                events_logger.debug(f'Word: "{word}" not found in message')