# Word-Counter-Bot

"Help people interested in this repository understand your project by adding a README"<br>
You are not interested in this bot...

## Description

Word-Counter-Bot is a Discord bot designed to count occurrences of specified words within messages. It allows users to add multiple words and admin users for tracking purposes.<br>
The bot offers various commands to facilitate word counting and management.

## Commands

- `/c`: Count occurrences of a word for a specific user. Example: `/c word user`
- `/hc`: Retrieve the highest count of a word. Example: `/hc word`
- `/thc`: Retrieve the total highest count of all words. `/thc`
- `/sw`: Show all tracked words. Example: `/sw`
- `/aw`: Add words to track (admin-only). Example: `/aw test test1 test2`
- `/rw`: Remove a word from tracking (admin-only). Example: `/rw test`

## How to run the bot

Word-Counter-Bot requires a configuration file (logging_config.yaml and bot_config.yaml) to run properly. (will be merged if possible)
Logging_config needs to be in the same directory as the main.exe. bot_config path needs to be passed as an argument.
Example: main.exe -p "C:\WordCounterBot\bot_config.yaml"

## Installation and Building

To build an executable (.exe) from a Python script, you can use pyinstaller:

1. Install pyinstaller using pip:
   ```
   pip install pyinstaller
   ```

2. Navigate to the directory containing your Python script (your_script.py) using the command line.

3. Run the following command to create the executable:
   ```
   pyinstaller --onefile your_script.py
   ```

   The `--onefile` option ensures the output is a single .exe file.