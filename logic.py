from collections import defaultdict
from unidecode import unidecode
import logging
import re

logic_logger = logging.getLogger('bot.logic')


async def scan(bot, server_id, word_counts=None, target_user_id=None, target_word=None):
    """
    Initiates a scan of all text channels in a server to count word occurrences.

    Args:
        bot (discord.Client): The Discord bot instance.
        server_id (int): The ID of the server to scan.
        word_counts (dict, optional): A dictionary to accumulate word counts. Defaults to None.
        target_user_id (int, optional): If provided, scans only for this user. Defaults to None.
        target_word (str, optional): If provided, scans for this word only. Defaults to None.
    """
    scan_type = "targeted" if target_user_id or target_word else "full"
    logic_logger.info(f"Starting {scan_type} scan - Server: {server_id}, User: {target_user_id}, Word: {target_word}")

    guild = bot.get_guild(server_id)
    word_counts = word_counts or defaultdict(lambda: defaultdict(int))
    words = [target_word] if target_word else await bot.db.get_words()
    total_messages_scanned = 0

    for channel in guild.text_channels:
        logic_logger.debug(f"Scanning channel: {channel.name} (ID: {channel.id})")
        messages_scanned = await scan_channel(channel, word_counts, words, target_user_id)
        total_messages_scanned += messages_scanned
        logic_logger.debug(f"Channel scan complete - {channel.name}: {messages_scanned} messages")

    await bot.db.raise_counts({
        (user_id, word): count
        for user_id, user_words in word_counts.items()
        for word, count in user_words.items()
    })
    logic_logger.info(f"Scan completed - Total messages: {total_messages_scanned}, Words tracked: {len(word_counts)}")


async def scan_channel(channel, word_counts, words, target_user_id=None) -> int:
    """
    Scans a channel and its threads for word occurrences.

    Args:
        channel (discord.TextChannel): The channel to scan.
        word_counts (dict): A dictionary to accumulate word counts.
        words (list): The words to count.
        target_user_id (int, optional): If provided, scans only for this user. Defaults to None.

    Returns:
        int: The number of messages scanned.
    """
    messages_scanned = await scan_messages(channel, word_counts, words, target_user_id)
    logic_logger.debug(f"Main channel scanned - {channel.name}: {messages_scanned} messages")

    threads = [thread async for thread in channel.archived_threads()] + channel.threads
    if threads:
        logic_logger.debug(f"Found {len(threads)} threads in {channel.name}")

    for thread in threads:
        logic_logger.debug(f"Scanning thread: {thread.name} (ID: {thread.id})")
        thread_messages_scanned = await scan_messages(thread, word_counts, words, target_user_id)
        messages_scanned += thread_messages_scanned
        logic_logger.debug(f"Thread scan complete - {thread.name}: {thread_messages_scanned} messages")

    return messages_scanned


async def scan_messages(channel, word_counts, words, target_user_id=None) -> int:
    """
    Scans messages in a channel or thread for word occurrences.

    Args:
        channel (discord.TextChannel or discord.Thread): The channel or thread to scan.
        word_counts (dict): A dictionary to accumulate word counts.
        words (list): The words to count.
        target_user_id (int, optional): If provided, scans only for this user. Defaults to None.

    Returns:
        int: The number of messages scanned.
    """
    messages_scanned = 0
    async for message in channel.history(limit=None):
        messages_scanned += 1
        if target_user_id and message.author.id != target_user_id:
            continue
        process_message(message, word_counts, words)
        if messages_scanned % 200 == 0:
            logic_logger.debug(f"Progress update - {channel.name}: {messages_scanned} messages scanned")
    return messages_scanned


def process_message(message, word_counts, words):
    """
    Processes a message to count occurrences of words.

    Args:
        message (discord.Message): The message to process.
        word_counts (dict): A dictionary to accumulate word counts.
        words (list): The words to count.
    """
    content_normalized = unidecode(message.content).lower()

    for word in words:
        if word:
            pattern = r'\b' + re.escape(word) + r'\b'
            matches = re.findall(pattern, content_normalized)
            count = len(matches)
            if count > 0:
                word_counts[message.author.id][word] += count
                logic_logger.debug(f"Word found - '{word}' ({count}x) by user {message.author.display_name}")

