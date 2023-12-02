import logging
import sqlite3


class SqlStatements:
    # logging setup
    _sql_logger = logging.getLogger('bot.sql')
    _sql_logger.debug('Logging setup complete')

    # sqlite connection
    try:
        _sql_logger.debug('Setting up sql connection')
        _sqlite_connection = sqlite3.connect('word_counter.db')
        cursor = _sqlite_connection.cursor()
        _sql_logger.debug('Setup of sql connection complete')
    except sqlite3.Error as error:
        _sql_logger.error(f'Connection to database failed: {error}')

    @staticmethod
    def _execute_query(query, success_message, error_message, params=None):
        try:
            with SqlStatements._sqlite_connection:
                if params:
                    SqlStatements.cursor.execute(query, params)
                else:
                    SqlStatements.cursor.executescript(query)
            SqlStatements._sql_logger.info(success_message)
        except sqlite3.Error as error:
            SqlStatements._sql_logger.error(f'{error_message}: {error}')

    @staticmethod
    def drop_tables():
        """drop all tables"""
        SqlStatements._sql_logger.debug('Dropping all tables')
        SqlStatements.cursor.execute('drop table user')
        SqlStatements.cursor.execute('drop table user_has_word')
        SqlStatements.cursor.execute('drop table word')
        SqlStatements._sql_logger.info('Dropped all tables')

    @staticmethod
    def create_tables():
        """create tables for database"""
        script = """
            -- create user table
            create table if not exists user (
                id integer primary key
            );
            
            -- create word table
            create table if not exists word (
                name text primary key
            );
            
            -- create user_has_word table
            create table if not exists user_has_word (
                user_id integer,
                word_name varchar(45),
                count integer,
                foreign key (user_id) references user (id),
                foreign key (word_name) references word (name)
            );"""
        SqlStatements._execute_query(
            script,
            'Tables created',
            'Failed to create tables'
        )

    @staticmethod
    def add_words(*words):
        """Add words to the database if they don't exist"""
        SqlStatements._sql_logger.debug('Inserting words into the database')

        for word in set(words):
            query = "insert or ignore into word values (:word);"
            SqlStatements._execute_query(
                query,
                f'Word: {word} successfully inserted',
                f'Failed to insert word: {word}',
                {'word': word}
            )

    def add_user_ids(*user_ids):
        """Add all server members to the database"""
        SqlStatements._sql_logger.debug('Inserting all users to the database')

        query = "insert or ignore into user values (:user_id)"
        for user_id in set(user_ids):
            SqlStatements._execute_query(
                query,
                f'User {user_id} inserted into the database',
                f'Error inserting user {user_id} to the database',
                {'user_id': user_id}
            )
        SqlStatements._sql_logger.debug('All members inserted into the database')

    @staticmethod
    def add_user_has_word(user_id, word, count):
        """Insert new user_has_word"""
        query = """
            insert into user_has_word values (
                :user_id,
                :word,
                :count
            );"""
        SqlStatements._execute_query(
            query,
            f'Inserted user_has_word record: {user_id} | {word} | {count}',
            'Error inserting user_has_word record',
            {'user_id': user_id, 'word': word, 'count': count}
        )

    @staticmethod
    def get_count(user_id, word):
        """Get count for a specific user_id and word"""
        SqlStatements._sql_logger.debug(f'Get count for user: {user_id} with word: {word}')
        try:
            with SqlStatements._sqlite_connection:
                count = SqlStatements.cursor.execute(
                    """select count from user_has_word
                    where user_id in (:user_id)
                    and word_name in (:word);""",
                    {'user_id': user_id, 'word': word}
                ).fetchone()[0]
        except Exception as error:
            SqlStatements._sql_logger.error(f'Error executing sql query: {error}')
            return None
        else:
            SqlStatements._sql_logger.info(f'Retrieved count: {count}')
            return count

    @staticmethod
    def get_words():
        """get all words from database"""
        SqlStatements._sql_logger.debug('Get all words from database')

        query = """select name from word"""
        success_message = 'Words retrieved successfully from the database'
        error_message = 'Error retrieving words from the database'

        with SqlStatements._sqlite_connection:
            words_database = SqlStatements._execute_query(
                query,
                success_message,
                error_message,
                fetch_result='all'
            )

        SqlStatements._sql_logger.info(f'Words from database: {words_database}')
        return words_database

    @staticmethod
    def get_all_users():
        """Get all user IDs from the database"""
        SqlStatements._sql_logger.debug('Get all users from database')
        try:
            with SqlStatements._sqlite_connection:
                users = SqlStatements.cursor.execute(
                    """select id from user;"""
                ).fetchall()

                user_ids = [user[0] for user in users]
                SqlStatements._sql_logger.info(f'All user IDs from database: {user_ids}')
                return user_ids
        except sqlite3.Error as error:
            SqlStatements._sql_logger.error(f'Error getting all users: {error}')
            return None

    @staticmethod
    def get_highest_count_column(word):
        """get user with the highest count"""
        SqlStatements._sql_logger.debug(f'Get user with highest count from word {word}')
        try:
            with SqlStatements._sqlite_connection:
                highest_count_column = SqlStatements.cursor.execute(
                    """select * from user_has_word
                        where count = (
                        select max(count) from user_has_word
                        where word_name = :word
                        )""",
                    {'word': word}
                ).fetchone()
        except TypeError as error:
            SqlStatements._sql_logger.error(error)
            return None
        SqlStatements._sql_logger.debug(f'Got highest count: {highest_count_column}')
        return highest_count_column

    @staticmethod
    def update_user_count(user_id, word, count):
        """Update user count"""
        SqlStatements._sql_logger.info('Updating count')
        with SqlStatements._sqlite_connection:
            # sum count
            if SqlStatements.check_user_has_word(user_id, word):
                current_count = SqlStatements.get_count(user_id, word)
                SqlStatements.cursor.execute(
                    """update user_has_word set count = :count
                    where user_id = :user_id
                    and word_name = :word;""",
                    {'count': current_count + count, 'user_id': user_id, 'word': word}
                )
                SqlStatements._sql_logger.info(f'Updated count of user: {current_count + count}')
            else:
                SqlStatements.add_user_has_word(user_id, word, count)

        SqlStatements._sql_logger.debug('Exiting insert_update_user_count')

    @staticmethod
    def check_user_has_word(user_id, word):
        """Check if user has association with word"""
        SqlStatements._sql_logger.debug('Check if user has association with word')

        with SqlStatements._sqlite_connection:
            exists = SqlStatements.cursor.execute(
                """select exists (
                    select 1 from user_has_word
                    where user_id = :user_id
                    and word_name = :word_name
                )""",
                {'user_id': user_id, 'word_name': word}
            ).fetchone()[0]

        SqlStatements._sql_logger.debug(
            f'User: {user_id} has association with word: {word}'
            if exists
            else f'User: {user_id} has no association with word: {word}'
        )
        return exists

    @staticmethod
    def get_total_highest_count_column():
        """Get the column with the highest count from user_has_word table"""
        try:
            with SqlStatements._sqlite_connection:
                thc_column = SqlStatements.cursor.execute(
                    """select * from user_has_word
                    order by count desc limit 1;"""
                ).fetchone()

                return thc_column
        except sqlite3.Error as error:
            SqlStatements._sql_logger.error(f'Error getting highest count column: {error}')

        SqlStatements._sql_logger.debug('No data found in user_has_word table.')
        return None
