import logging.config
import sqlite3
import unittest
import yaml
import sql


class TestDatabaseModule(unittest.TestCase):
    _logger = None

    @classmethod
    def setUpClass(cls):
        # Loading logging config
        with open('logging_config.yaml', 'rt') as config_file:
            logging_config = yaml.safe_load(config_file.read())

        logging.config.dictConfig(logging_config)
        cls._logger = logging.getLogger('unittest')

    def setUp(self):
        # Create a connection to database
        self._connection = sqlite3.connect(':memory:')
        self._cursor = self._connection.cursor()

        self._logger.debug('help')


if __name__ == '__main__':
    unittest.main()
