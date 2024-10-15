import logging
import sqlite3
from typing import Optional, List, Tuple, Dict, Any
from config import DB_PATH


class SqlStatements:
    """
    Class containing SQL statements and methods for executing them.
    """
    _sql_logger = logging.getLogger('bot.sql')
    _sql_logger.info('Logging setup complete')

    @staticmethod
    def _get_connection():
        """
        Establishes a connection to the SQLite database.

        Returns:
            sqlite3.Connection: A connection object to the SQLite database.

        Raises:
            sqlite3.Error: If the connection to the database fails.
        """
        try:
            SqlStatements._sql_logger.debug('Setting up sql connection')
            connection = sqlite3.connect(DB_PATH)
            return connection
        except sqlite3.Error as error:
            SqlStatements._sql_logger.error(f'Connection to database failed: {error}')
            raise

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

        Args:
            query (str): The SQL query to execute.
            success_message (str): Message to log on successful execution.
            error_message (str): Message to log on execution error.
            params (Optional[Dict[str, Any]]): Parameters for the SQL query.
            fetch_one (bool): If True, fetch only one result.

        Returns:
            Optional[List[Tuple]]: The query results or None if an error occurred.
        """
        connection = None
        cursor = None
        try:
            connection = SqlStatements._get_connection()
            cursor = connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            result = cursor.fetchone() if fetch_one else cursor.fetchall()
            connection.commit()
            SqlStatements._sql_logger.debug(success_message)
            return result

        except sqlite3.Error as error:
            SqlStatements._sql_logger.error(f'{error_message}: {error}')
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @staticmethod
    def drop_tables():
        """
        Drop all tables from the database.
        Only for unit_tests.
        """
        SqlStatements._sql_logger.debug('Dropping all tables')
        queries = [
            'drop table if exists user',
            'drop table if exists user_has_word',
            'drop table if exists word'
        ]
        for query in queries:
            SqlStatements._execute_query(query, 'Dropped table', 'Failed to drop table')

    @staticmethod
    def create_tables():
        """
        Create tables for the database.
        """
        table_scripts = {
            "user": """
                create table if not exists user (
                    id integer primary key,
                    permission text check (permission in ('admin', 'user'))
                );""",
            "word": """
                create table if not exists word (
                    name text primary key
                );""",
            "user_has_word": """
                create table if not exists user_has_word (
                    user_id integer,
                    word_name varchar(45),
                    count integer,
                    foreign key (user_id) references user (id),
                    foreign key (word_name) references word (name)
                );"""
        }
        for name, script in table_scripts.items():
            SqlStatements._execute_query(
                script,
                f'{name.capitalize()} table created',
                f'Failed to create {name} table'
            )

    @staticmethod
    def add_words(*words):
        """
        Add words to the database if they don't exist.

        Args:
            *words: Variable length argument list of words to add.
        """
        SqlStatements._sql_logger.debug('Inserting words into the database')
        query = "insert or ignore into word values (:word);"
        for word in set(words):
            SqlStatements._execute_query(
                query,
                f'Word: {word} successfully inserted',
                f'Error inserting word: {word}',
                {'word': word}
            )

    @staticmethod
    def add_user_ids(*user_ids):
        """
        Add user IDs to the database if they don't exist.

        Args:
            *user_ids: Variable length argument list of user IDs to add.
        """
        SqlStatements._sql_logger.debug('Inserting all users to the database')
        query = "insert or ignore into user values (:user_id, 'user')"
        for user_id in set(user_ids):
            SqlStatements._execute_query(
                query,
                f'User {user_id} inserted into the database',
                f'Error inserting user ID: {user_id}',
                {'user_id': user_id}
            )

    @staticmethod
    def add_admins(*user_ids: int) -> None:
        """
        Add admin permission to the specific user IDs.

        Args:
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

        Args:
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

        Args:
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

        Args:
            user_id (int): The ID of the user.
            word (str): The word to get the count for.

        Returns:
            int | None: The count of the word for the user, or None if an error occurred.
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

        Args:
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

        Args:
            user_id (int): The ID of the user.
            word (str): The word to update the count for.
            count (int): The count to add to the existing count.
        """
        SqlStatements._sql_logger.debug('Updating count')
        query = """
            INSERT INTO user_has_word (user_id, word_name, count)
            VALUES (:user_id, :word, :count)
            ON CONFLICT(user_id, word_name) DO UPDATE SET count = user_has_word.count + :count;
        """
        SqlStatements._execute_query(
            query,
            f'Updated count for user: {user_id} with word: {word}',
            f'Error updating count for user: {user_id} with word: {word}',
            {'user_id': user_id, 'word': word, 'count': count}
        )

    @staticmethod
    def check_user_has_word(user_id: int, word: str) -> bool:
        """
        Check if a user has an association with a specific word.

        Args:
            user_id (int): The ID of the user.
            word (str): The word to check for association.

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
        return bool(exists[0])

    @staticmethod
    def check_user_is_admin(user_id: int) -> bool:
        """
        Check if a user has admin privileges.

        Args:
            user_id (int): The ID of the user to check.

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
            fetch_one=True
        )
        return permission[0] == 'admin'

    @staticmethod
    def get_user_word_counts(user_id: int) -> List[Tuple[str, int]]:
        """
        Get all words and their counts for a specific user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            List[Tuple[str, int]]: A list of tuples containing words and their counts for the user.
        """
        SqlStatements._sql_logger.debug(f'Get all words and counts for user: {user_id}')
        query = """
            select word_name, count from user_has_word
            where user_id = :user_id
        """
        result = SqlStatements._execute_query(
            query,
            f'Successfully retrieved words and counts for user: {user_id}',
            f'Error retrieving words and counts for user: {user_id}',
            {'user_id': user_id},
            fetch_one=False
        )
        return result if result else []
