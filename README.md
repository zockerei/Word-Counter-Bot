# Word-Counter-Bot

A Discord bot designed to count occurrences of specified words within messages. You are not interested in this bot...

## Description

Word-Counter-Bot is a Discord bot that tracks and counts specific words used by server members. It allows administrators to add and remove words for tracking purposes and provides various commands for users to check word counts and statistics.

## Project Structure

word-counter-bot/
├── src/
│ ├── main.py
│ ├── config.py
│ └── sql.py
├── config/
│ ├── bot_config.yaml
│ └── logging_config.yaml
├── db/
│ └── word_counter.db (created automatically)
└── logs/
└── bot.log (created automatically)

## Commands

- `/c <word> <user>`: Count occurrences of a word for a specific user
- `/hc <word>`: Retrieve the highest count of a word
- `/thc`: Retrieve the total highest count of all words
- `/sw`: Show all tracked words
- `/aw <word>`: Add word to database (admin-only)
- `/rw <word>`: Remove a word from database (admin-only)
- `/h`: Show bot usage instructions

## Setup and Configuration

1. Ensure you have Python 3.11 or later installed.
2. Install required dependencies:
   ```
   pip install discord.py pyyaml
   ```
3. Create a `config/bot_config.yaml` file with the following structure:
   ```yaml
   token: "YOUR_BOT_TOKEN"
   words:
     - "word1"
     - "word2"
   server_id: YOUR_SERVER_ID
   channel_id: YOUR_CHANNEL_ID
   admin_ids:
     - ADMIN_USER_ID_1
     - ADMIN_USER_ID_2
   ```
4. Create a `config/logging_config.yaml` file for logging configuration.
5. Run the bot using:
   ```
   python src/main.py
   ```

## Autostart with Windows Fluent Terminal

To set up autostart using Windows Fluent Terminal:

1. Add a new profile in the terminal settings.
2. Configure the command line:
   - Command Line: `C:\path\to\your\src\main.py`
   - Starting Directory: `C:\path\to\your\bot\directory`

Adjust other settings as needed.

## Notes

- The bot uses SQLite for data storage (db/word_counter.db).
- Logs are stored in the logs/bot.log file.
- The bot requires appropriate Discord permissions to function correctly.
- Ensure the bot has access to read message history for accurate counting.