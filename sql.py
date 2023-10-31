import logging.config
import sqlite3
import yaml


class SqlStatements:
    # import logging_config
    with open('logging_config.yaml', 'rt') as config_file:
        logging_config = yaml.safe_load(config_file.read())

    # logging setup
    logging.config.dictConfig(logging_config)
    sql_logger = logging.getLogger('bot.sql')
    sql_logger.debug('logging setup complete')

    # sqlite connection
    try:
        sql_logger.debug('setting up sql connection')
        sqlite_connection = sqlite3.connect('users.db')
        cursor = sqlite_connection.cursor()
        sql_logger.debug('setup of sql connection complete')
    except sqlite3.Error as error:
        sql_logger.error(f'Connection to database failed: {error}')

    @staticmethod
    def create_table():
        """create table users for database"""
        SqlStatements.sql_logger.debug('in create table')
        with SqlStatements.sqlite_connection:
            SqlStatements.sql_logger.debug('creating table if not exists')
            SqlStatements.cursor.execute("""create table if not exists users (
                            user_id integer primary key,
                            count integer
                            )""")

    @staticmethod
    def insert_update_user_count(user_id, count):
        """Check message for the word and add it to the database"""
        with SqlStatements.sqlite_connection:
            SqlStatements.sql_logger.debug('select user_id')
            SqlStatements.cursor.execute("select user_id from users where user_id = :user_id",
                                         {'user_id': user_id})
            SqlStatements.sql_logger.debug('user_id selected')

        if SqlStatements.cursor.fetchall():
            """if user is already in database, sum count"""
            SqlStatements.sql_logger.info('user is in database. Updating...')
            with SqlStatements.sqlite_connection:
                SqlStatements.sql_logger.debug('get count')
                current_count = SqlStatements.cursor.execute("select count from users where user_id = :user_id",
                                                             {'user_id': user_id}).fetchone()[0]
                SqlStatements.sql_logger.debug('got count')

                SqlStatements.cursor.execute("update users set count = :count where user_id = :user_id",
                                             {'count': current_count + count, 'user_id': user_id})
                SqlStatements.sql_logger.info('updated count of user')
        else:
            with SqlStatements.sqlite_connection:
                SqlStatements.sql_logger.info('user not found. Inserting...')
                SqlStatements.cursor.execute("insert into users values (:user_id, :count)",
                                             {'user_id': user_id, 'count': count})
                SqlStatements.sql_logger.info('new user inserted')
        SqlStatements.sql_logger.debug('exiting insert_update_user_count')
