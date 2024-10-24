from collections import defaultdict
from unidecode import unidecode
import logging
import db.queries as queries
from bot import bot
import asyncio

logic_logger = logging.getLogger('bot.logic')

async def scan(server_id, word_counts=None, target_user_id=None, target_word=None):
    """
    General scan method for server, user, or word.

    Args:
        server_id (int): The ID of the server to scan.
        word_counts (dict, optional): A dictionary to accumulate word counts.
        target_user_id (int, optional): If provided, scans only for this user.
        target_word (str, optional): If provided, scans for this word only.
    """
    logic_logger.info(f"Starting scan. User: {target_user_id}, Word: {target_word}, Server: {server_id}")
    guild = bot.get_guild(server_id)
    word_counts = word_counts or defaultdict(lambda: defaultdict(int))
    total_messages_scanned = 0

    tasks = []
    for channel in guild.text_channels:
        task = asyncio.create_task(scan_channel(channel, word_counts, target_user_id, target_word))
        tasks.append(task)

    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)
    total_messages_scanned = sum(results)

    queries.update_word_counts(word_counts)
    logic_logger.info(f"Scan completed. Total messages scanned: {total_messages_scanned}")

async def scan_channel(channel, word_counts, target_user_id=None, target_word=None):
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
    messages_scanned = await scan_messages(channel, word_counts, target_user_id, target_word)

    # Scan messages in the channel's threads
    threads = [thread async for thread in channel.archived_threads()] + channel.threads
    for thread in threads:
        messages_scanned += await scan_messages(thread, word_counts, target_user_id, target_word)

    return messages_scanned

async def scan_messages(channel, word_counts, target_user_id=None, target_word=None):
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
        process_message(message, word_counts, target_word)
    return messages_scanned

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
    
    words_to_check = [target_word] if target_word else queries.get_words()

    for word in words_to_check:
        if word and word in content_normalized:
            word_counts[message.author.id][word] += content_normalized.count(word)

def update_word_counts(word_counts):
    """
    Updates the database with word counts, only if the new count is higher.

    Args:
        word_counts (dict): A dictionary containing word counts for users.
    """
    for user_id, update_words in word_counts.items():
        for word, update_count in update_words.items():
            current_count = queries.get_count(user_id, word)
            if current_count is None:
                queries.add_user_has_word(user_id, word, update_count)
            elif update_count > current_count:
                queries.update_user_count(user_id, word, update_count - current_count)
