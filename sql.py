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
    def _execute_query(query, success_message='Success', error_message='Error', params=None, fetch_one=None):
        try:
            with SqlStatements._sqlite_connection:
                if params:
                    SqlStatements.cursor.execute(query, params)
                else:
                    SqlStatements.cursor.execute(query)

                if fetch_one:
                    result = SqlStatements.cursor.fetchone()
                else:
                    result = SqlStatements.cursor.fetchall()

                SqlStatements._sql_logger.debug(success_message)
                return result

        except sqlite3.Error as error:
            SqlStatements._sql_logger.error(f'{error_message}: {error}')

    @staticmethod
    def drop_tables():
        """drop all tables"""
        SqlStatements._sql_logger.debug('Dropping all tables')
        SqlStatements.cursor.execute('drop table if exists user')
        SqlStatements.cursor.execute('drop table if exists user_has_word')
        SqlStatements.cursor.execute('drop table if exists word')
        SqlStatements._sql_logger.info('Dropped all tables')

    @staticmethod
    def create_tables():
        """create tables for database"""
        # Create user table
        user_table_script = """
            create table if not exists user (
                id integer primary key,
                permission text check (permission in ('admin', 'user'))
            );"""
        SqlStatements._execute_query(
            user_table_script,
            'User table created',
            'Failed to create user table'
        )
        # Create word table
        word_table_script = """
            create table if not exists word (
                name text primary key
            );"""
        SqlStatements._execute_query(
            word_table_script,
            'Word table created',
            'Failed to create word table'
        )
        # Create user_has_word table
        user_has_word_table_script = """
            create table if not exists user_has_word (
                user_id integer,
                word_name varchar(45),
                count integer,
                foreign key (user_id) references user (id),
                foreign key (word_name) references word (name)
            );"""
        SqlStatements._execute_query(
            user_has_word_table_script,
            'User_has_word table created',
            'Failed to create user_has_word table'
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

    @staticmethod
    def add_user_ids(*user_ids):
        """Add all server members to the database"""
        SqlStatements._sql_logger.debug('Inserting all users to the database')

        query = "insert or ignore into user values (:user_id, 'user')"
        for user_id in set(user_ids):
            SqlStatements._execute_query(
                query,
                f'User {user_id} inserted into the database',
                f'Error inserting user {user_id} to the database',
                {'user_id': user_id}
            )
        SqlStatements._sql_logger.debug('All members inserted into the database')

    @staticmethod
    def add_admin(user_id):
        """Add admin to the specific id"""
        SqlStatements._sql_logger.debug(f'Adding admin to admin_id: {user_id}')

        query = """update user
                set permission = 'admin'
                where id = :user_id;"""

        SqlStatements._execute_query(
            query,
            f'{user_id} is now admin',
            f'Failed to make {user_id} admin',
            {'user_id': user_id}
        )

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
    def remove_word(word):
        """Remove word from database"""
        query = "delete from word where name = :word;"

        SqlStatements._execute_query(
            query,
            f'Removed word: {word} successfully',
            f'Error removing word: {word}',
            {'word': word}
        )

    @staticmethod
    def get_count(user_id, word):
        """Get count for a specific user_id and word"""
        SqlStatements._sql_logger.debug(f'Get count for user: {user_id} with word: {word}')

        query = """select count from user_has_word
                   where user_id = :user_id
                   and word_name = :word;"""

        count = SqlStatements._execute_query(
            query,
            f'Retrieved count for user: {user_id} with word: {word}',
            f'Error getting count for user: {user_id} with word: {word}',
            {'user_id': user_id, 'word': word},
            True
        )
        SqlStatements._sql_logger.debug(f'Count: {count}')
        if count is None:
            return None
        return count[0]

    @staticmethod
    def get_words():
        """get all words from database"""
        SqlStatements._sql_logger.debug('Get all words from database')

        words_database = [word[0] for word in SqlStatements._execute_query(
            """select * from word""",
            'Words retrieved successfully from the database',
            'Error retrieving words from the database',
            fetch_one=False
        )]
        SqlStatements._sql_logger.info(f'Words from database: {words_database}')
        return words_database

    @staticmethod
    def get_all_users():
        """Get all user IDs from the database"""
        SqlStatements._sql_logger.debug('Get all users from database')

        user_ids = SqlStatements._execute_query(
            """select id from user;""",
            'All user IDs successfully retrieved from the database',
            'Error getting all users',
            fetch_one=False
        )
        user_ids = [user[0] for user in user_ids]

        SqlStatements._sql_logger.info(f'User_ids from database: {user_ids}')

        return user_ids

    @staticmethod
    def get_highest_count_column(word):
        """get user with the highest count"""
        query = """
            select * from user_has_word
            where count = (
                select max(count) from user_has_word
                where word_name = :word
            )"""

        result = SqlStatements._execute_query(
            query,
            f'Got highest count for word {word}',
            f'Error while getting highest count for word {word}',
            {'word': word},
            fetch_one=True
        )
        SqlStatements._sql_logger.debug(f'Result: {result}')
        return result
    
    @staticmethod
    def get_total_highest_count_column():
        """Get the column with the highest count from user_has_word table"""
        query = """select * from user_has_word
                   order by count desc limit 1;"""

        result = SqlStatements._execute_query(
            query,
            'Successfully retrieved highest count column.',
            'Error getting highest count column',
            fetch_one=True
        )
        return result

    @staticmethod
    def update_user_count(user_id, word, count):
        """Update user count"""
        SqlStatements._sql_logger.info('Updating count')
        if SqlStatements.check_user_has_word(user_id, word):
            current_count = SqlStatements.get_count(user_id, word)

            query = """update user_has_word
                        set count = :count
                        where user_id = :user_id
                        and word_name = :word;"""

            SqlStatements._execute_query(
                query,
                f'Updated count of user: {current_count + count}',
                params={'count': current_count + count, 'user_id': user_id, 'word': word}
            )
        else:
            SqlStatements.add_user_has_word(user_id, word, count)

        SqlStatements._sql_logger.debug('Exiting update_user_count')

    @staticmethod
    def check_user_has_word(user_id, word):
        """Check if user has association with word"""
        SqlStatements._sql_logger.debug('Check if user has association with word')

        query = """select exists (
                     select 1 from user_has_word
                     where user_id = :user_id
                     and word_name = :word
                     )"""

        exists = SqlStatements._execute_query(
            query,
            f'Success in check_user_has_word',
            f'Error in check_user_has_word',
            {'user_id': user_id, 'word': word},
            fetch_one=True
        )
        SqlStatements._sql_logger.debug(f'Result: {exists}')
        return exists[0]

    @staticmethod
    def check_user_is_admin(user_id):
        """Check if user has admin privileges"""
        SqlStatements._sql_logger.debug(f'Check if user has admin privileges')

        query = """select permission from user
                where id = :user_id"""

        permission = SqlStatements._execute_query(
            query,
            f'Success in check_user_is_admin',
            f'Error in check_user_is_admin',
            {'user_id': user_id},
            True
        )[0]
        SqlStatements._sql_logger.debug(f'Permission: {permission}')
        if permission == 'admin':
            SqlStatements._sql_logger.debug(f'User {user_id} has admin privileges')
            return True
        else:
            SqlStatements._sql_logger.debug(f'User {user_id} has no admin privileges')
            return False
