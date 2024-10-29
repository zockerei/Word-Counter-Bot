import discord
from discord.ext import commands
from discord import Embed, Color, app_commands
import logging
import db.queries as queries

bot_logger = logging.getLogger('cogs.general')


class GeneralCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """
        Initializes the GeneralCommands cog.

        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot
        bot_logger.info('General commands cog initialized')

    @app_commands.command(name="c", description="Count occurrences of a word for a specific user")
    async def count(self, interaction: discord.Interaction, word: str, user: discord.Member):
        """
        Counts occurrences of a word for a specific user.

        Args:
            interaction (discord.Interaction): The interaction object.
            word (str): The word to count.
            user (discord.Member): The user to check.
        """
        await interaction.response.defer()
        bot_logger.info(f'Count requested - User: {user.display_name}, Word: {word}, '
                        f'Requester: {interaction.user.display_name}')

        converted_user_id = user.id
        count_user_id = queries.get_count(converted_user_id, word)
        username = user.display_name

        if count_user_id is None:
            bot_logger.info(f'No count found for {username} with word: {word}')
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

        highest_count_tuple = queries.get_highest_count_column(word)
        highest_count_user = self.bot.get_user(highest_count_tuple[0]).display_name
        count_embed.set_footer(text=f'The person who has said {word} the most is '
                                    f'{highest_count_user} with {highest_count_tuple[2]} times. '
                                    'Imagine 🐕💦')
        await interaction.followup.send(embed=count_embed)
        bot_logger.debug('Count message sent')

    @app_commands.command(name="hc", description="Retrieve the highest count of a word")
    async def highest_count(self, interaction: discord.Interaction, word: str):
        """
        Retrieves the highest count of a word across all users.

        Args:
            interaction (discord.Interaction): The interaction object.
            word (str): The word to check.
        """
        await interaction.response.defer()
        bot_logger.info(f'Highest count requested - Word: {word}, Requester: {interaction.user.display_name}')
        highest_count_tuple = queries.get_highest_count_column(word)

        if highest_count_tuple is None:
            bot_logger.info(f'No counts found for word: {word}')
            no_count_embed = Embed(
                title='Dead Server',
                description=f"""No User in this Server has said {word}\n
                Or the word is not being monitored :eyes:""",
                color=Color.red()
            )
            await interaction.followup.send(embed=no_count_embed)
            return

        bot_logger.debug(f'Highest count found - User: {highest_count_tuple[0]}, Count: {highest_count_tuple[2]}')
        username = self.bot.get_user(highest_count_tuple[0]).display_name
        highest_count_embed = Embed(
            title='Highest count from all Users',
            description=f"""The user who has said {word} the most is {username}\n
            With an impressive amount of {highest_count_tuple[2]} times""",
            color=Color.gold()
        )
        await interaction.followup.send(embed=highest_count_embed)
        bot_logger.debug('Highest count message sent')

    @app_commands.command(name="thc", description="Retrieve the total highest count of all words")
    async def total_highest_count_command(self, interaction: discord.Interaction):
        """
        Retrieves the total highest count of all words across all users.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        await interaction.response.defer()
        bot_logger.info(f'Total highest count requested by {interaction.user.display_name}')
        highest_count_result = queries.get_total_highest_count_column()

        if highest_count_result is None:
            bot_logger.info('No counts found in database')
            no_count_embed = Embed(
                title='Dead Server',
                description="""No User in this Server has said any word...\n
                Or they tricked the system (not hard)""",
                color=Color.red()
            )
            await interaction.followup.send(embed=no_count_embed)
            return

        bot_logger.debug(f'Total highest count found - User: {highest_count_result[0]}, '
                         f'Word: {highest_count_result[1]}, Count: {highest_count_result[2]}')
        username = self.bot.get_user(highest_count_result[0]).display_name
        thc_embed = Embed(
            title='Highest count of all words',
            description=f"""The winner for the Highest count of all words is... {username}!\n
            Who has said {highest_count_result[1]} {highest_count_result[2]} times""",
            color=Color.gold()
        )
        await interaction.followup.send(embed=thc_embed)
        bot_logger.debug('Total highest count message sent')

    @app_commands.command(name="sw", description="Show all tracked words")
    async def show_words(self, interaction: discord.Interaction):
        """
        Shows all tracked words in the database.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        await interaction.response.defer()
        bot_logger.info(f'Show words requested by {interaction.user.display_name}')
        words_database = queries.get_words()

        words_embed = Embed(
            title='All words',
            description=f"""Here is a list of all the words you should rather not say...\n
            {', '.join(words_database)}""",
            color=Color.blue()
        )
        await interaction.followup.send(embed=words_embed)
        bot_logger.debug('Words list message sent')

    @app_commands.command(name="h", description="Show bot usage instructions")
    async def help_command(self, interaction: discord.Interaction):
        """
        Shows bot usage instructions.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        await interaction.response.defer()
        bot_logger.debug(f'Help requested by {interaction.user.display_name}')
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
        bot_logger.debug('Help message sent')

    @app_commands.command(name="uwc", description="Show all words and their counts for a specific user")
    async def user_word_counts(self, interaction: discord.Interaction, member: discord.Member):
        """
        Shows all words and their counts for a specific user.

        Args:
            interaction (discord.Interaction): The interaction object.
            member (discord.Member): The user to check.
        """
        await interaction.response.defer()
        bot_logger.info(f'User word counts requested - Target: {member.display_name}, '
                        f'Requester: {interaction.user.display_name}')

        user_id = member.id
        word_counts = queries.get_user_word_counts(user_id)

        if not word_counts:
            bot_logger.info(f'No word counts found for user: {member.display_name}')
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
        bot_logger.debug('Word counts message sent')


async def setup(bot):
    """
    Set up the GeneralCommands cog.

    Args:
        bot: The Discord bot instance to add this cog to
    """
    await bot.add_cog(GeneralCommands(bot))
    bot_logger.info('General commands cog loaded')
