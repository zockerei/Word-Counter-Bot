"""The bot's slash commands."""

from __future__ import annotations

import logging

import discord
from discord import Color, Embed, app_commands

from counting import normalize

logger = logging.getLogger('bot.commands')

# Longer lists would get cut off by Discord's embed size limit.
MAX_LIST_LINES = 25
MEDALS = ['🥇', '🥈', '🥉']


async def tracked_words(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    """Suggest tracked words while typing."""
    current = normalize(current)
    return [
        app_commands.Choice(name=word, value=word)
        for word in interaction.client.patterns
        if current in word
    ][:25]


def ranked(lines: list[str]) -> str:
    shown = [
        f'{MEDALS[i] if i < len(MEDALS) else f"{i + 1}."} {line}'
        for i, line in enumerate(lines[:MAX_LIST_LINES])
    ]
    if len(lines) > MAX_LIST_LINES:
        shown.append(f'…and {len(lines) - MAX_LIST_LINES} more')
    return '\n'.join(shown)


@app_commands.command(name='count', description='How often someone said a word')
@app_commands.describe(user='Who to check', word='Leave empty to see all their words')
@app_commands.autocomplete(word=tracked_words)
async def count(interaction: discord.Interaction, user: discord.Member, word: str | None = None):
    db = interaction.client.db
    if word is None:
        counts = await db.user_counts(user.id)
        if not counts:
            embed = Embed(
                title=f'{user.display_name} is clean',
                description=f"{user.mention} hasn't said any tracked words.",
                color=Color.green(),
            )
        else:
            embed = Embed(
                title=f'Word counts of {user.display_name}',
                description=ranked([f'{word}: {amount}' for word, amount in counts]),
                color=Color.blue(),
            )
        await interaction.response.send_message(embed=embed)
        return

    word = normalize(word)
    amount = await db.get_count(user.id, word)
    if not amount:
        embed = Embed(
            title=f'{user.display_name} is clean',
            description=f'{user.mention} has said {word} 0 times\n(Or he tricked the system)',
            color=Color.green(),
        )
    else:
        top_user_id, top_count = (await db.word_ranking(word))[0]
        embed = Embed(
            title=f'Count from {user.display_name}',
            description=f'{user.mention} has said {word} {amount} times\n\n'
                        f'The person who has said {word} the most is <@{top_user_id}> '
                        f'with {top_count} times. Imagine 🐕💦',
            color=Color.blue(),
        )
    await interaction.response.send_message(embed=embed)


@app_commands.command(name='top', description='Who said a word the most')
@app_commands.describe(word='Leave empty for the highest counts of all words')
@app_commands.autocomplete(word=tracked_words)
async def top(interaction: discord.Interaction, word: str | None = None):
    db = interaction.client.db
    if word is None:
        rows = await db.top_counts(10)
        lines = [f'<@{user_id}>: {word} {amount} times' for user_id, word, amount in rows]
        title = 'Highest counts of all words'
    else:
        word = normalize(word)
        rows = await db.word_ranking(word)
        lines = [f'<@{user_id}>: {amount}' for user_id, amount in rows]
        title = f'Who said "{word}" the most'

    if not lines:
        embed = Embed(
            title='Dead Server',
            description='Nobody in this server has said that yet...\n'
                        'Or the word is not being tracked :eyes:',
            color=Color.red(),
        )
    else:
        embed = Embed(title=title, description=ranked(lines), color=Color.gold())
    await interaction.response.send_message(embed=embed)


@app_commands.command(name='words', description='List the tracked words')
async def words(interaction: discord.Interaction):
    tracked = ', '.join(interaction.client.patterns) or 'No words yet. Add one with /addword.'
    embed = Embed(
        title='All words',
        description=f'Here is a list of all the words you should rather not say...\n\n{tracked}',
        color=Color.blue(),
    )
    await interaction.response.send_message(embed=embed)


@app_commands.command(name='addword', description='Start tracking a word (admin)')
@app_commands.describe(word='A word or phrase, spaces are fine')
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
        description=f'Now tracking **{word}**.\n'
                    f'Counting old messages, this can take a while.',
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


@app_commands.command(
    name='removeword', description='Stop tracking a word and delete its counts (admin)'
)
@app_commands.describe(word='The word to remove')
@app_commands.autocomplete(word=tracked_words)
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
        title='Word removed',
        description=f'Stopped tracking **{word}** and deleted its counts.',
        color=Color.red(),
    ))


@app_commands.command(name='help', description='Show all commands')
async def help_command(interaction: discord.Interaction):
    embed = Embed(
        title='Word Counter Bot',
        description='I count how often everyone says the tracked words.\n\n'
                    '`/count user [word]` How often someone said a word, '
                    'or all their words if you leave the word empty\n'
                    '`/top [word]` Who said a word the most, '
                    'or the highest counts of all words\n'
                    '`/words` List the tracked words\n'
                    '`/addword word` Start tracking a word (admin)\n'
                    '`/removeword word` Stop tracking a word (admin)',
        color=Color.blue(),
    ).set_footer(text='Use these commands wisely!')
    await interaction.response.send_message(embed=embed)


def register(tree: app_commands.CommandTree) -> None:
    for command in (count, top, words, add_word, remove_word, help_command):
        tree.add_command(command)
