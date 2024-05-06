# Word-Counter-Bot

"Help people interested in this repository understand your project by adding a README"<br>
You are not interested in this bot...

## Description

Word-Counter-Bot is a Discord bot designed to count occurrences of specified words within messages. It allows users to add multiple words and admin users for tracking purposes.<br>
I did not test the bot in linux, although im sure it works. Just use the main, sql and embed.py

## Commands

- `/c`: Count occurrences of a word for a specific user. Example: `/c word user`
- `/hc`: Retrieve the highest count of a word. Example: `/hc word`
- `/thc`: Retrieve the total highest count of all words. `/thc`
- `/sw`: Show all tracked words. Example: `/sw`
- `/aw`: Add word to database (admin-only). Example: `/aw test`
- `/rw`: Remove a word from database (admin-only). Example: `/rw test`

## How to run the bot

Word-Counter-Bot requires a configuration file (config.yaml) to run<br>
config path needs to be passed as an argument `-p`<br>
Example config.yaml in repository

# Autostart with Windows Fluent Terminal

To set up autostart using Windows Fluent Terminal, follow these steps:

## Step 1: Add a New Profile to Terminal

Create a new profile in the terminal settings.

## Step 2: Configure Command Line

Specify the command line. For example:

- **Command Line Example:** `C:\wordcounter\main.exe`
- **Starting Directory:** Not necessary

Note: Merely putting `main.exe` in the command line and having the starting directory as `C:\wordcounter` doesn't work. Adjust other settings as per your preference.

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