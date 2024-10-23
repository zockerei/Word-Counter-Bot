from pathlib import Path
import yaml
import logging.config

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Log file path
LOG_FOLDER_PATH = BASE_DIR / 'logs'
LOG_FOLDER_PATH.mkdir(parents=True, exist_ok=True)
CONFIG_FOLDER_PATH = BASE_DIR / 'config'

# Database file path
DB_PATH = 'sqlite:///' + str(BASE_DIR / 'instance' / 'word_counter.db')
DB_PATH.mkdir(parents=True, exist_ok=True)

# ENV file path
ENV_PATH = BASE_DIR / 'instance' / '.env'

# Cog folder path
COG_FOLDER_PATH = BASE_DIR / 'bot' / 'cogs'

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

    words, server_id, channel_id, admin_ids, disable_initial_scan = (
        bot_config['words'],
        bot_config['server_id'], 
        bot_config['channel_id'],
        bot_config['admin_ids'],
        bot_config.get('disable_initial_scan', True)
    )

    return words, server_id, channel_id, admin_ids, disable_initial_scan
