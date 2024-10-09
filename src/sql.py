import logging
import sqlite3
from typing import Optional, List, Tuple, Dict, Any
from config import DB_PATH


class SqlStatements:
    """
    Class containing SQL statements and methods for executing them.
    """
    # logging setup
    _sql_logger = logging.getLogger('bot.sql')
    _sql_logger.info('Logging setup complete')

    # sqlite connection
    try:
        _sql_logger.debug('Setting up sql connection')
        _sqlite_connection = sqlite3.connect(DB_PATH)
        cursor = _sqlite_connection.cursor()
        _sql_logger.info('Setup of sql connection complete')
    except sqlite3.Error as error:
        _sql_logger.error(f'Connection to database failed: {error}')

    @staticmethod
    def _execute_query(
            query: str,
            success_message: str = 'Success',
            error_message: str = 'Error',
            params: Optional[Dict[str, Any]] = None,
            fetch_one: bool = False,
    ) -> Optional[List[Tuple]]:
        """
        Execute a SQL query and return the result.

        Parameters:
            query (str): The SQL query to execute.
            success_message (str, optional): Success message to log. Defaults to 'Success'.
            error_message (str, optional): Error message to log. Defaults to 'Error'.
            params (Dict[str, Any], optional): Parameters for the query as a dictionary of parameter names
                and values. Defaults to None.
            fetch_one (bool, optional): Whether to fetch only one result. Defaults to False.

        Returns:
            Optional[List[Tuple]]: A list of tuples containing the result of the query, or None if an error occurred.
        """
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
            return None

    @staticmethod
    def drop_tables():
        """
        Drop all tables from the database.
        Only for unit_tests
        """
        SqlStatements._sql_logger.debug('Dropping all tables')
        SqlStatements.cursor.execute('drop table if exists user')
        SqlStatements.cursor.execute('drop table if exists user_has_word')
        SqlStatements.cursor.execute('drop table if exists word')
        SqlStatements._sql_logger.info('Dropped all tables')

    @staticmethod
    def create_tables():
        """
        Create tables for the database.
        """
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
        """
        Add words to the database if they don't exist.

        Parameters:
            *words (str): Words to add to the database.
        """
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
        """
        Add user IDs to the database if they don't exist.

        Parameters:
            *user_ids (int): User IDs to add to the database.
        """
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
    def add_admins(*user_ids: int) -> None:
        """
        Add admin permission to the specific user IDs.

        Parameters:
            *user_ids (int): The IDs of the users to be granted admin permission.
        """
        SqlStatements._sql_logger.debug('Adding admins')

        query = """update user
                set permission = 'admin'
                where id = :user_id;"""

        for user_id in set(user_ids):
            SqlStatements._execute_query(
                query,
                f'{user_id} is now admin',
                f'Failed to make {user_id} admin',
                {'user_id': user_id}
            )

        SqlStatements._sql_logger.debug('Admins added successfully')

    @staticmethod
    def add_user_has_word(user_id: int, word: str, count: int) -> None:
        """
        Insert a new user_has_word record.

        Parameters:
            user_id (int): The ID of the user.
            word (str): The word to be associated with the user.
            count (int): The count of the word for the user.
        """
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
    def remove_word(word: str) -> None:
        """
        Remove a word from the database.

        Parameters:
            word (str): The word to be removed.
        """
        query = "delete from word where name = :word;"

        SqlStatements._execute_query(
            query,
            f'Removed word: {word} successfully',
            f'Error removing word: {word}',
            {'word': word}
        )

    @staticmethod
    def get_count(user_id: int, word: str) -> int | None:
        """
        Get the count for a specific user ID and word.

        Parameters:
            user_id (int): The ID of the user.
            word (str): The word to get the count for.

        Returns:
            Optional[int]: The count of the word for the user, or None if an error occurred.
        """
        SqlStatements._sql_logger.debug(f'Get count for user: {user_id} with word: {word}')

        query = """select count from user_has_word
                   where user_id = :user_id
                   and word_name = :word;"""

        count = SqlStatements._execute_query(
            query,
            f'Retrieved count for user: {user_id} with word: {word}',
            f'Error getting count for user: {user_id} with word: {word}',
            {'user_id': user_id, 'word': word}
        )
        if not count:
            return None
        SqlStatements._sql_logger.debug(count)
        return count[0][0]

    @staticmethod
    def get_words():
        """
        Get all words from the database.

        Returns:
            List[str]: A list containing all words retrieved from the database.
        """
        SqlStatements._sql_logger.debug('Get all words from database')

        words_database = [word[0] for word in SqlStatements._execute_query(
            """select * from word""",
            'Words retrieved successfully from the database',
            'Error retrieving words from the database',
            fetch_one=False
        )]
        return words_database

    @staticmethod
    def get_all_users() -> List[int]:
        """
        Get all user IDs from the database.

        Returns:
            List[int]: A list of user IDs retrieved from the database.
        """
        SqlStatements._sql_logger.debug('Get all users from database')

        user_ids = SqlStatements._execute_query(
            """select id from user;""",
            'All user IDs successfully retrieved from the database',
            'Error getting all users',
            fetch_one=False
        )
        user_ids = [user[0] for user in user_ids]
        return user_ids

    @staticmethod
    def get_highest_count_column(word: str) -> Tuple | None:
        """
        Get user with the highest count for a specific word.

        Parameters:
            word (str): The word for which to find the user with the highest count.

        Returns:
            Tuple | None: A tuple representing the user with the highest count for the given word.
        """
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
        return result

    @staticmethod
    def get_total_highest_count_column() -> Tuple | None:
        """
        Get the column with the highest count from user_has_word table.

        Returns:
            Tuple | None: A tuple representing the row with the highest count in the user_has_word table.
        """
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
    def update_user_count(user_id: int, word: str, count: int) -> None:
        """
        Update user count for a specific word.

        Parameters:
            user_id (int): The ID of the user.
            word (str): The word to update the count for.
            count (int): The count to update.
        """
        SqlStatements._sql_logger.debug('Updating count')
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

    @staticmethod
    def check_user_has_word(user_id: int, word: str) -> tuple:
        """
        Check if a user has an association with a specific word.

        Parameters:
            user_id (int): The ID of the user.
            word (str): The word to check association with.

        Returns:
            bool: True if the user has an association with the word, False otherwise.
        """
        SqlStatements._sql_logger.debug('Check if user has association with word')

        query = """select exists (
                     select 1 from user_has_word
                     where user_id = :user_id
                     and word_name = :word
                     )"""

        exists = SqlStatements._execute_query(
            query,
            f'User: {user_id} has association with the word: {word}',
            f'Error in check_user_has_word',
            {'user_id': user_id, 'word': word},
            fetch_one=True
        )
        return exists[0]

    @staticmethod
    def check_user_is_admin(user_id: int) -> bool:
        """
        Check if a user has admin privileges.

        Parameters:
            user_id (int): The ID of the user.

        Returns:
            bool: True if the user has admin privileges, False otherwise.
        """
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
        if permission == 'admin':
            SqlStatements._sql_logger.debug(f'User {user_id} has admin privileges')
            return True
        else:
            SqlStatements._sql_logger.debug(f'User {user_id} has no admin privileges')
            return False
