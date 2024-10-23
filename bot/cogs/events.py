from discord.ext import commands
import db.queries as queries
from discord import Color, Embed
from unidecode import unidecode
import logging
import discord
from config import load_bot_config

events_logger = logging.getLogger('cogs.events')

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.token, self.words, self.server_id, self.channel_id, self.admin_ids, self.disable_initial_scan = load_bot_config()
        events_logger.debug('Events cog initialized')

    @commands.Cog.listener()
    async def on_ready(self):
        # Sync commands with a specific guild (server_id)
        guild = discord.Object(id=self.server_id)
        self.bot.tree.copy_global_to(guild=guild)
        await self.bot.tree.sync(guild=guild)
        events_logger.info('Command tree synced with specific guild')

        queries.create_tables()
        queries.add_words(*self.words)
        queries.add_user_ids(*[member.id for member in self.bot.get_guild(self.server_id).members])
        queries.add_admins(*self.admin_ids)

        if not self.disable_initial_scan:
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

        await self.bot.get_channel(self.channel_id).send(embed=new_user_embed)

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

def setup(bot):
    bot.add_cog(Events(bot))
