import discord
from discord import Embed, Color
from discord.ext import commands
import logging
from bot.database import get_db
from bot.bot import admin_ids

bot_logger = logging.getLogger('cogs.admin')
sql_statements = queries.SqlStatements()

class AdminCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="aw", description="Add a word to the database (admin-only)")
    @commands.describe(word="The word to add")
    async def add_word(self, interaction: discord.Interaction, word: str):
        """
        Add a word to the database (admin-only).
        """
        await interaction.response.defer()

        if sql_statements.check_user_is_admin(interaction.user.id):
            sql_statements.add_words(word)
            await self.bot.scan(target_word=word)
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
            await self.permission_abuse(interaction)

    @commands.command(name="rw", description="Remove a word from the database (admin-only)")
    @commands.describe(word="The word to remove")
    async def remove_word(self, interaction: discord.Interaction, word: str):
        """
        Remove a word from the database (admin-only).
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
            await self.permission_abuse(interaction)

    async def permission_abuse(self, interaction: discord.Interaction):
        """
        Send a mod abuse message when a user without permissions attempts an admin action.
        """
        bot_logger.debug('Permission abuse')
        admin_users = [self.bot.get_user(admin_id).display_name for admin_id in admin_ids]
        admin_list = ', '.join(admin_users)
        mod_abuse_embed = Embed(
            title='No permission',
            description=f"""You have no permission to perform this action\n
            Call the admins: {admin_list}""",
            color=Color.red()
        )
        await interaction.followup.send(embed=mod_abuse_embed)
        bot_logger.info('Message for mod abuser sent')

def setup(bot):
    bot.add_cog(AdminCommands(bot))
