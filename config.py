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
    """
    Sets up the logging configuration for the application.

    Reads the logging configuration from a YAML file and applies it.
    Updates the log file paths for rotating and error logs.

    Raises:
        FileNotFoundError: If the logging configuration file is not found.
        yaml.YAMLError: If there is an error parsing the YAML file.
        Exception: For any other unexpected errors.
    """
    try:
        with open(CONFIG_FOLDER_PATH / 'logging_config.yaml', 'r') as file:
            config = yaml.safe_load(file.read())

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
    """
    Singleton class to load and provide bot configuration.

    Attributes:
        token (str): The bot token.
        words (list): A list of words to track.
        server_id (int): The ID of the server.
        channel_id (int): The ID of the channel.
        admin_ids (list): A list of admin user IDs.
        disable_initial_scan (bool): Flag to disable initial scan.
    """

    _instance = None

    def __new__(cls):
        """
        Creates a new instance of BotConfig if it doesn't exist.

        Returns:
            BotConfig: The singleton instance of BotConfig.
        """
        if cls._instance is None:
            cls._instance = super(BotConfig, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """
        Loads configuration from a YAML file.

        Raises:
            FileNotFoundError: If the bot configuration file is not found.
            yaml.YAMLError: If there is an error parsing the YAML file.
            Exception: For any other unexpected errors.
        """
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
    """
    Gets the singleton instance of BotConfig.

    Returns:
        BotConfig: The singleton instance of BotConfig.
    """
    return BotConfig()
