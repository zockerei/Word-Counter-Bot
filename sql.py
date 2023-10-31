import logging.config
import sqlite3


class SqlStatements:
    @staticmethod
    def logging_setup(logging_config):
        # logging setup
        logging.config.dictConfig(logging_config)
        sql_logger = logging.getLogger('bot.sql')
        sql_logger.debug('logging setup complete')

    @staticmethod
    def create_table():
        try:
            # sql_logger.debug('setting up sql connection')
            sqlite_connection = sqlite3.connect('users.db')
            cursor = sqlite_connection.cursor()

            with sqlite_connection:
                # sql_logger.debug('creating table if not exists')
                cursor.execute("""create table if not exists users (
                                user_id integer primary key,
                                count integer
                                )""")
        except sqlite3.Error as error:
            print(error)
            # sql_logger.error(f'Connection to database failed: {error}')
        else:
            if sqlite_connection:
                sqlite_connection.close()
                # sql_logger.info('Database ready and connection closed')
