import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Environment-specific settings
ENV = os.getenv('ENV', 'development')

# Common settings
LOGGING_CONFIG_PATH = BASE_DIR / 'config' / 'logging_config.yaml'
BOT_CONFIG_PATH = BASE_DIR / 'config' / 'bot_config.yaml'

# Environment-specific settings
if ENV == 'production':
    DB_PATH = BASE_DIR / 'word_counter.db'
else:
    DB_PATH = BASE_DIR / 'db' / 'word_counter.db'

# Ensure the database directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Log file path
LOG_FILE_PATH = BASE_DIR / 'bot.log'
LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)