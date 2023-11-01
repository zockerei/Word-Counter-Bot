import logging
import sqlite3


class SqlStatements:
    # logging setup
    sql_logger = logging.getLogger('bot.sql')
    sql_logger.debug('Logging setup complete')

    # sqlite connection
    try:
        sql_logger.debug('Setting up sql connection')
        sqlite_connection = sqlite3.connect('users.db')
        cursor = sqlite_connection.cursor()
        sql_logger.debug('Setup of sql connection complete')
    except sqlite3.Error as error:
        sql_logger.error(f'Connection to database failed: {error}')

    @staticmethod
    def create_table():
        """create table users for database"""
        SqlStatements.sql_logger.debug('In create table')
        with SqlStatements.sqlite_connection:
            SqlStatements.sql_logger.debug('Creating table if not exists')
            SqlStatements.cursor.execute("""create table if not exists users (
                            user_id integer primary key,
                            count integer
                            )""")

    @staticmethod
    def add_guild_members(guild_members):
        """add all server members to database"""
        SqlStatements.sql_logger.debug('Inserting all users to database')
        for user_id in guild_members:
            if not SqlStatements.check_user(user_id):
                SqlStatements.insert_new_user(user_id, 0)

    @staticmethod
    def get_count(user_id):
        """get count of user_id"""
        SqlStatements.sql_logger.debug('Get count')
        with SqlStatements.sqlite_connection:
            count = SqlStatements.cursor.execute("select count from users where user_id = :user_id",
                                                 {'user_id': user_id}).fetchone()[0]
            SqlStatements.sql_logger.info(f'User count is: {count}')
        return count

    @staticmethod
    def insert_new_user(user_id, count):
        """insert new user into database"""
        with SqlStatements.sqlite_connection:
            SqlStatements.sql_logger.debug(f'Inserting new user {user_id}')
            SqlStatements.cursor.execute("insert into users values (:user_id, :count)",
                                         {'user_id': user_id, 'count': count})
            SqlStatements.sql_logger.info(f'User {user_id} inserted to database')

    @staticmethod
    def check_user(user_id):
        # check if user is in database
        with SqlStatements.sqlite_connection:
            # get user_id
            SqlStatements.sql_logger.debug('Select user_id')
            SqlStatements.cursor.execute("select user_id from users where user_id = :user_id",
                                         {'user_id': user_id})
            SqlStatements.sql_logger.debug('User_id selected')

        if SqlStatements.cursor.fetchall():
            # if user is already in database, return True
            SqlStatements.sql_logger.debug(f'User {user_id} is in database')
            return True
        else:
            SqlStatements.sql_logger.debug(f'User {user_id} not in database')
            return False

    @staticmethod
    def update_user_count(user_id, count):
        """Update user count"""
        SqlStatements.sql_logger.info('Updating count')
        with SqlStatements.sqlite_connection:
            # sum count
            current_count = SqlStatements.get_count(user_id)

            SqlStatements.cursor.execute("update users set count = :count where user_id = :user_id",
                                         {'count': current_count + count, 'user_id': user_id})
            SqlStatements.sql_logger.info('Updated count of user')
        SqlStatements.sql_logger.debug('Exiting insert_update_user_count')
