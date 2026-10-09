# Word-Counter-Bot

A Discord bot that counts how often each member says the words you choose.

- Counts every tracked word in every new message. Matching ignores case and accents, and only counts whole words, so `cat` doesn't match `concatenate`. Phrases with spaces work too.
- Posts a message the first time someone says a word.
- When you add a word, it also counts that word in all old messages, including threads and forum posts.
- Stores the counts in your PostgreSQL database.

## Commands

| Command | |
|---|---|
| `/count user [word]` | How often someone said a word. Leave the word empty to see all their words |
| `/top [word]` | Who said a word the most. Leave the word empty for the highest counts of all words |
| `/words` | List the tracked words |
| `/addword word` | Start tracking a word and count it in old messages (admin) |
| `/removeword word` | Stop tracking a word and delete its counts (admin) |
| `/help` | Show all commands |

`/addword` and `/removeword` need the **Manage Server** permission. To let other people or roles use them, go to **Server Settings → Integrations → Word-Counter-Bot**.

## Discord setup

1. Create an application in the [Discord Developer Portal](https://discord.com/developers/applications).
2. Under **Bot**, copy the token and turn on **Message Content Intent** and **Server Members Intent**.
3. Under **OAuth2 → URL Generator**, select the `bot` and `applications.commands` scopes, and these permissions:
   - View Channels
   - Send Messages
   - Send Messages in Threads
   - Embed Links
   - Read Message History

   This is permission integer `274877991936`.
4. Open the generated URL to add the bot to your server.

To get a server or channel ID, turn on **Developer Mode** in Discord's advanced settings, then right-click the server or channel and choose **Copy ID**.

## Configuration

Copy `.env.example` to `.env` and fill it in:

```env
DISCORD_TOKEN=your-discord-bot-token

# The server the bot counts words in.
GUILD_ID=123456789012345678

# Optional. Channel for the welcome message when someone joins. Leave it empty for no message.
WELCOME_CHANNEL_ID=

# Set to true to count the full server history on startup. Words added with /addword
# are always counted in the history, so this is only needed after the bot was offline.
SCAN_HISTORY=false

DATABASE_URL=postgresql://user:password@192.168.0.10:5432/word_counter

# Docker only. The bot's IP on the br0 network. Pick a free one outside your router's DHCP range.
BOT_IP=192.168.0.51

# Optional. DEBUG, INFO, WARNING or ERROR. Defaults to INFO.
LOG_LEVEL=INFO
```

Create the database before the first start, for example with `CREATE DATABASE word_counter;`. The bot creates its tables itself. If the database password contains special characters such as `@`, `:` or `/`, URL-encode them (`@` becomes `%40`).

## Running

### Docker

```sh
docker compose up -d
```

This pulls the prebuilt image from GHCR. Logs are kept in the `logs` volume.

The container joins the existing `br0` network (Unraid's custom network) with the IP from `BOT_IP`. This lets it reach a database container that has its own IP on `br0`, which containers on the default bridge network cannot.

### Windows

Run `run.bat`. It creates a virtual environment and installs the requirements on first run, then starts the bot.

### Manually

Requires Python 3.12 or newer.

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt   # Windows: .venv\Scripts\pip
.venv/bin/python bot.py                     # Windows: .venv\Scripts\python
```

Run the tests with `python -m unittest`.

## The database

| Table | |
|---|---|
| `words` | The tracked words, lowercase and without accents |
| `word_counts` | One row per user and word: `user_id`, `word`, `count` |

Removing a word deletes its counts. Counts stay when someone leaves the server.
