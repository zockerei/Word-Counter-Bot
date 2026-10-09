"""The bot's slash commands."""

from __future__ import annotations

import logging

import discord
from discord import Color, Embed, app_commands

from counting import normalize

logger = logging.getLogger('bot.commands')


@app_commands.command(name='c', description='Count occurrences of a word for a specific user')
async def count(interaction: discord.Interaction, word: str, user: discord.Member):
    bot = interaction.client
    word = normalize(word)
    amount = await bot.db.get_count(user.id, word)
    if not amount:
        embed = Embed(
            title=f'{user.display_name} is clean',
            description=f'{user.mention} has said {word} 0 times\n(Or he tricked the system)',
            color=Color.green(),
        )
    else:
        top_user_id, top_count = (await bot.db.word_ranking(word))[0]
        embed = Embed(
            title=f'Count from {user.display_name}',
            description=f'{user.mention} has said {word} {amount} times\n\n'
                        f'The person who has said {word} the most is <@{top_user_id}> '
                        f'with {top_count} times. Imagine 🐕💦',
            color=Color.blue(),
        )
    await interaction.response.send_message(embed=embed)


@app_commands.command(name='hc', description='Retrieve the highest count of a word')
async def highest_count(interaction: discord.Interaction, word: str):
    word = normalize(word)
    ranking = await interaction.client.db.word_ranking(word)
    if not ranking:
        embed = Embed(
            title='Dead Server',
            description=f'No User in this Server has said {word}\n'
                        f'Or the word is not being monitored :eyes:',
            color=Color.red(),
        )
    else:
        user_id, amount = ranking[0]
        embed = Embed(
            title='Highest count from all Users',
            description=f'The user who has said {word} the most is <@{user_id}>\n'
                        f'With an impressive amount of {amount} times',
            color=Color.gold(),
        )
    await interaction.response.send_message(embed=embed)


@app_commands.command(name='thc', description='Retrieve the total highest count of all words')
async def total_highest_count(interaction: discord.Interaction):
    top = await interaction.client.db.top_counts(1)
    if not top:
        embed = Embed(
            title='Dead Server',
            description='No User in this Server has said any word...\n'
                        'Or they tricked the system (not hard)',
            color=Color.red(),
        )
    else:
        user_id, word, amount = top[0]
        embed = Embed(
            title='Highest count of all words',
            description=f'The winner for the Highest count of all words is... <@{user_id}>!\n'
                        f'Who has said {word} {amount} times',
            color=Color.gold(),
        )
    await interaction.response.send_message(embed=embed)


@app_commands.command(name='sw', description='Show all tracked words')
async def show_words(interaction: discord.Interaction):
    embed = Embed(
        title='All words',
        description='Here is a list of all the words you should rather not say...\n\n'
                    + ', '.join(interaction.client.patterns),
        color=Color.blue(),
    )
    await interaction.response.send_message(embed=embed)


@app_commands.command(name='uwc', description='Show all words and their counts for a specific user')
async def user_word_counts(interaction: discord.Interaction, member: discord.Member):
    counts = await interaction.client.db.user_counts(member.id)
    if not counts:
        embed = Embed(
            title=f'{member.display_name} has no words',
            description=f"{member.mention} hasn't said any tracked words.",
            color=Color.red(),
        )
    else:
        embed = Embed(
            title=f'Word counts for {member.display_name}',
            description='\n'.join(f'{word}: {amount}' for word, amount in counts),
            color=Color.blue(),
        )
    await interaction.response.send_message(embed=embed)


@app_commands.command(name='wuc', description='Show all users and their counts for a specific word')
async def word_user_counts(interaction: discord.Interaction, word: str):
    word = normalize(word)
    ranking = await interaction.client.db.word_ranking(word)
    if not ranking:
        embed = Embed(
            title=f'No users found for "{word}"',
            description=f"No users have said the word '{word}' yet.",
            color=Color.red(),
        )
    else:
        embed = Embed(
            title=f'User counts for "{word}"',
            description='\n'.join(f'<@{user_id}>: {amount}' for user_id, amount in ranking),
            color=Color.blue(),
        )
    await interaction.response.send_message(embed=embed)


@app_commands.command(name='aw', description='Add a word to the database (admin-only)')
@app_commands.default_permissions(manage_guild=True)
async def add_word(interaction: discord.Interaction, word: str):
    bot = interaction.client
    word = normalize(word)
    if not word:
        await interaction.response.send_message('That word is empty.', ephemeral=True)
        return
    if not await bot.db.add_word(word):
        await interaction.response.send_message(f'"{word}" is already tracked.', ephemeral=True)
        return
    await bot.reload_words()
    logger.info('%s added the word "%s"', interaction.user, word)
    await interaction.response.send_message(embed=Embed(
        title='Word added',
        description=f'Word that was added to the database:\n{word}\n\n'
                    f'Counting old messages now, this can take a while.',
        color=Color.green(),
    ))
    bot.run_in_background(_count_new_word(interaction, word))


async def _count_new_word(interaction: discord.Interaction, word: str) -> None:
    # Sent to the channel, not as a followup: those expire after 15 minutes.
    try:
        result = await interaction.client.count_history([word])
    except Exception:
        logger.exception('Counting old messages for "%s" failed', word)
        await interaction.channel.send(f'Counting old messages for "{word}" failed.')
        return
    users = len(result.counts)
    total = sum(result.counts.values())
    await interaction.channel.send(
        f'Done counting **{word}**: found {total} times from {users} users '
        f'in {result.messages:,} messages.'
    )


@app_commands.command(name='rw', description='Remove a word from the database (admin-only)')
@app_commands.default_permissions(manage_guild=True)
async def remove_word(interaction: discord.Interaction, word: str):
    bot = interaction.client
    word = normalize(word)
    if not await bot.db.remove_word(word):
        await interaction.response.send_message(f'"{word}" is not tracked.', ephemeral=True)
        return
    await bot.reload_words()
    logger.info('%s removed the word "%s"', interaction.user, word)
    await interaction.response.send_message(embed=Embed(
        title='Removed word',
        description=f'Removed word from database:\n{word}',
        color=Color.red(),
    ))


@app_commands.command(name='h', description='Show bot usage instructions')
async def help_command(interaction: discord.Interaction):
    embed = Embed(
        title='Word Counter Bot Help',
        description='Here are the available commands:\n\n'
                    '/c [word] [user]: Count occurrences of a word for a specific user.\n'
                    '/hc [word]: Retrieve the highest count of a word.\n'
                    '/thc: Retrieve the total highest count of all words.\n'
                    '/sw: Show all tracked words.\n'
                    '/aw [word]: Add word to database (admin-only).\n'
                    '/rw [word]: Remove a word from database (admin-only).\n'
                    '/uwc [user]: Show all words and their counts for a specific user.\n'
                    '/wuc [word]: Show all users and their counts for a specific word.',
        color=Color.blue(),
    ).set_footer(text='Use these commands wisely!')
    await interaction.response.send_message(embed=embed)


def register(tree: app_commands.CommandTree) -> None:
    for command in (
        count, highest_count, total_highest_count, show_words, user_word_counts,
        word_user_counts, add_word, remove_word, help_command,
    ):
        tree.add_command(command)
