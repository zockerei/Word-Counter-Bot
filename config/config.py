from pathlib import Path
import yaml
import logging.config

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Log file path
LOG_FOLDER_PATH = BASE_DIR / 'logs'
LOG_FOLDER_PATH.mkdir(parents=True, exist_ok=True)
CONFIG_FOLDER_PATH = BASE_DIR / 'config'

# Common settings
DB_PATH = BASE_DIR / 'db' / 'word_counter.db'

# Ensure the database directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Function to load the logging configuration
def setup_logging():
    """Setup logging configuration"""
    try:
        with open(CONFIG_FOLDER_PATH / 'logging_config.yaml', 'r') as file:
            config = yaml.safe_load(file.read())

        # Update log file paths
        config['handlers']['rotating_file']['filename'] = str(LOG_FOLDER_PATH / 'bot.log')
        config['handlers']['error_file']['filename'] = str(LOG_FOLDER_PATH / 'errors.log')

        logging.config.dictConfig(config)
    except FileNotFoundError:
        print(f"Logging configuration file not found: {CONFIG_FOLDER_PATH / 'logging_config.yaml'}")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
    except Exception as e:
        print(f"Unexpected error in Logging Configuration: {e}")

# Function to load the bot configuration
def load_bot_config():
    """Loads bot configuration from a YAML file.

    Returns:
        tuple: A tuple containing the bot token, archiving status, folder path, and channel IDs.
    """
    with open(CONFIG_FOLDER_PATH / 'bot_config.yaml', 'r') as config_file:
        config = yaml.safe_load(config_file)
        bot_config = config

    token, words, server_id, channel_id, admin_ids, disable_initial_scan = (
        bot_config['token'],
        bot_config['words'],
        bot_config['server_id'], 
        bot_config['channel_id'],
        bot_config['admin_ids'],
        bot_config.get('disable_initial_scan', True)
    )

    return token, words, server_id, channel_id, admin_ids, disable_initial_scan
