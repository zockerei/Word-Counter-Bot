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
    def drop_tables():
        """drop all tables"""
        SqlStatements._sql_logger.debug('Dropping all tables')
        SqlStatements.cursor.execute('drop table user')
        SqlStatements.cursor.execute('drop table user_has_word')
        SqlStatements.cursor.execute('drop table word')
        SqlStatements._sql_logger.info('Dropped all tables')

    @staticmethod
    def create_tables():
        """create table users for database"""
        SqlStatements._sql_logger.debug('In create tables')
        try:
            with SqlStatements._sqlite_connection:
                # user table
                SqlStatements._sql_logger.debug('Creating table user')
                SqlStatements.cursor.execute(
                    """create table if not exists user (
                    id integer primary key
                    );"""
                )
                SqlStatements._sql_logger.debug('Creating table word')
                # word table
                SqlStatements.cursor.execute(
                    """create table if not exists word (
                    name text primary key
                    );"""
                )
                SqlStatements._sql_logger.debug('Creating table user_has_word')
                # user_has_word table
                SqlStatements.cursor.execute(
                    """create table if not exists user_has_word (
                    user_id integer,
                    word_name varchar(45),
                    count integer,
                    foreign key (user_id) references user (id),
                    foreign key (word_name) references word (name)
                    );"""
                )
        except sqlite3.Error as error:
            SqlStatements._sql_logger.error(f'Error creating table: {error}')

    @staticmethod
    def add_words(*words):
        """Add words to the database if they don't exist"""
        SqlStatements._sql_logger.debug('Inserting words into the database')

        for word in set(words):
            try:
                SqlStatements.cursor.execute(
                    """insert or ignore into word values (:word)""",
                    {'word': word}
                )
                SqlStatements._sql_logger.debug(f'Added word {word} into the database')
            except sqlite3.IntegrityError:
                SqlStatements._sql_logger.debug(f'Word: {word} already in the database')

        SqlStatements._sql_logger.info('All words in the database')

    def add_user_ids(*user_ids):
        """Add all server members to the database"""
        SqlStatements._sql_logger.debug('Inserting all users to the database')

        for user_id in set(user_ids):
            try:
                SqlStatements.cursor.execute(
                    "insert or ignore into user values (:user_id)",
                    {'user_id': user_id}
                )
                SqlStatements._sql_logger.info(f'User {user_id} inserted into the database')
            except sqlite3.Error as error:
                SqlStatements._sql_logger.error(f'Error inserting user {user_id} to the database: {error}')

        SqlStatements._sql_logger.info('All members inserted into the database')

    @staticmethod
    def get_count(user_id, word):
        """get count of user_id"""
        SqlStatements._sql_logger.debug(f'Get count from user: {user_id} with word: {word}')
        try:
            with SqlStatements._sqlite_connection:
                count = SqlStatements.cursor.execute(
                    """select count from user_has_word
                    inner join user on user.id = user_has_word.user_id
                    inner join word on word.name = user_has_word.word_name
                    where user_id = :user_id
                    and word_name = :word;""",
                    {'user_id': user_id, 'word': word}
                ).fetchone()[0]
        except TypeError as error:
            SqlStatements._sql_logger.error(error)
            return -1
        else:
            SqlStatements._sql_logger.info(f'User count is: {count}')
            return count

    @staticmethod
    def get_words():
        """get all words from database"""
        SqlStatements._sql_logger.debug('Get all words from database')
        with SqlStatements._sqlite_connection:
            words_database = [
                word[0] for word in SqlStatements.cursor.execute(
                    """select name from word"""
                ).fetchall()
            ]
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
            return -1
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
                SqlStatements.insert_user_has_word(user_id, word, count)

        SqlStatements._sql_logger.debug('Exiting insert_update_user_count')

    @staticmethod
    def check_user_has_word(user_id, word):
        """check if user has association with word"""
        SqlStatements._sql_logger.debug('Check if user has association with word')

        with SqlStatements._sqlite_connection:
            SqlStatements._sql_logger.debug(f'Select user {user_id} from user_has_word')
            SqlStatements.cursor.execute(
                """select * from user_has_word
                where user_id = :user_id
                and word_name = :word_name""",
                {'user_id': user_id, 'word_name': word}
            )
            SqlStatements._sql_logger.debug(f'User with id: {user_id} selected')

        if SqlStatements.cursor.fetchall():
            # if user has association in database, return True
            SqlStatements._sql_logger.debug(f'User: {user_id} has association with word: {word}')
            return True
        else:
            SqlStatements._sql_logger.debug(f'User: {user_id} has no association with word: {word}')
            return False

    @staticmethod
    def insert_user_has_word(user_id, word, count):
        """insert new user-word"""
        SqlStatements._sql_logger.debug(f'Insert new user_has_word user_id: {user_id} word: {word} count: {count}')
        with SqlStatements._sqlite_connection:
            SqlStatements.cursor.execute(
                """insert into user_has_word values(
                :user_id,
                :word,
                :count);""",
                {'user_id': user_id, 'word': word, 'count': count}
            )

    @staticmethod
    def get_total_highest_count_column():
        """Get the column with the highest count from user_has_word table"""
        try:
            with SqlStatements._sqlite_connection:
                thc_column = SqlStatements.cursor.execute(
                    """SELECT * FROM user_has_word
                    ORDER BY count DESC LIMIT 1;"""
                ).fetchone()

                if thc_column:
                    user_id, word_name, count = thc_column
                    return thc_column
                else:
                    SqlStatements._sql_logger.debug('No data found in user_has_word table.')
                    return None
        except sqlite3.Error as error:
            SqlStatements._sql_logger.error(f'Error getting highest count column: {error}')
            return None
