import discord
from discord import Embed, Color, app_commands
from discord.ext import commands
import logging
from config import get_bot_config
import db.queries as queries
from logic import scan

bot_logger = logging.getLogger('cogs.admin')

class AdminCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = get_bot_config()

    @app_commands.command(name="aw", description="Add a word to the database (admin-only)")
    async def add_word(self, interaction: discord.Interaction, word: str):
        """
        Add a word to the database (admin-only).
        """
        await interaction.response.defer()

        if queries.check_user_is_admin(interaction.user.id):
            queries.add_words(word)
            await scan(self.config.server_id, target_word=word)
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

    @app_commands.command(name="rw", description="Remove a word from the database (admin-only)")
    async def remove_word(self, interaction: discord.Interaction, word: str):
        """
        Remove a word from the database (admin-only).
        """
        await interaction.response.defer()
        bot_logger.debug(f'Removing word: {word} from database')

        if queries.check_user_is_admin(interaction.user.id):
            queries.remove_word(word)
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
        admin_users = [self.bot.get_user(admin_id).display_name for admin_id in self.config.admin_ids]
        admin_list = ', '.join(admin_users)
        mod_abuse_embed = Embed(
            title='No permission',
            description=f"""You have no permission to perform this action\n
            Call the admins: {admin_list}""",
            color=Color.red()
        )
        await interaction.followup.send(embed=mod_abuse_embed)
        bot_logger.info('Message for mod abuser sent')

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
    bot_logger.debug('Admin commands loaded')
