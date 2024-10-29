from pathlib import Path
import yaml
import logging.config

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Log file path
LOG_FOLDER_PATH = BASE_DIR / 'logs'
LOG_FOLDER_PATH.mkdir(parents=True, exist_ok=True)
CONFIG_FOLDER_PATH = BASE_DIR / 'config'

# Database file path
DB_PATH = 'sqlite:///' + str(BASE_DIR / 'instance' / 'word_counter.db')

# Cog folder path
COG_FOLDER_PATH = BASE_DIR / 'cogs'


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
        logging.error(f"Logging configuration file not found: {CONFIG_FOLDER_PATH / 'logging_config.yaml'}")
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in Logging Configuration: {e}")


class BotConfig:
    """Singleton class to load and provide bot configuration."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BotConfig, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(CONFIG_FOLDER_PATH / 'bot_config.yaml', 'r') as config_file:
                config = yaml.safe_load(config_file)
                self.token = config['token']
                self.words = config['words']
                self.server_id = config['server_id']
                self.channel_id = config['channel_id']
                self.admin_ids = config['admin_ids']
                self.disable_initial_scan = config.get('disable_initial_scan', True)
        except FileNotFoundError:
            logging.error(f"Bot configuration file not found: {CONFIG_FOLDER_PATH / 'bot_config.yaml'}")
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML file: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in Bot Configuration: {e}")


def get_bot_config():
    """Get the singleton instance of BotConfig."""
    return BotConfig()
