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
        _cursor = _sqlite_connection.cursor()
        _sql_logger.debug('Setup of sql connection complete')
    except sqlite3.Error as error:
        _sql_logger.error(f'Connection to database failed: {error}')

    @staticmethod
    def test():
        """dropping tables"""
        # drop table
        SqlStatements._cursor.execute('drop table user')
        SqlStatements._cursor.execute('drop table user_has_word')
        SqlStatements._cursor.execute('drop table word')

        # create table
        SqlStatements.create_table()

        # inserts
        SqlStatements._cursor.execute('insert into user values (372045873095639040);')
        SqlStatements._cursor.execute('insert into word values ("test");')
        SqlStatements._cursor.execute(
            """insert into user_has_word values (
            372045873095639040,
            "test",
            50);"""
        )

        # select test
        print(SqlStatements._cursor.execute('select * from user').fetchall())
        print(SqlStatements._cursor.execute('select * from word').fetchall())
        print(SqlStatements._cursor.execute('select * from user_has_word').fetchall())

    @staticmethod
    def create_table():
        """create table users for database"""
        SqlStatements._sql_logger.debug('In create table')
        with SqlStatements._sqlite_connection:
            # user table
            SqlStatements._sql_logger.debug('Creating table user')
            SqlStatements._cursor.execute(
                """create table if not exists user (
                id integer primary key,
                foreign key (id) references user_has_word (user_id)
                );"""
            )
            SqlStatements._sql_logger.debug('Creating table word')
            # word table
            SqlStatements._cursor.execute(
                """create table if not exists word (
                name text primary key,
                foreign key (name) references user_has_word (word_name)
                );"""
            )
            SqlStatements._sql_logger.debug('Creating table user_has_word')
            # user_has_word table
            SqlStatements._cursor.execute(
                """create table if not exists user_has_word (
                user_id integer,
                word_name varchar(45),
                count integer
                );"""
            )

    @staticmethod
    def add_words(words):
        """add all words to database"""
        SqlStatements._sql_logger.debug('Inserting all words to database')
        for word in words:
            # add check for unique
            SqlStatements._cursor.execute(
                "insert into word values (:word)",
                {'word': word}
            )
            SqlStatements._sql_logger.debug(f'added word {word} into database')

        SqlStatements._sql_logger.info('All words in database')

    @staticmethod
    def add_guild_members(guild_members):
        """add all server members to database"""
        SqlStatements._sql_logger.debug('Inserting all users to database')
        for user_id in guild_members:
            if not SqlStatements.check_user(user_id):
                SqlStatements.insert_new_user(user_id)
        SqlStatements._sql_logger.info('All members in database')

    @staticmethod
    def get_count(user_id, word):
        """get count of user_id"""
        SqlStatements._sql_logger.debug('Get count')
        with SqlStatements._sqlite_connection:
            count = SqlStatements._cursor.execute(
                """select count from user_has_word
                inner join user on user.id = user_has_word.user_id
                inner join word on word.name = user_has_word.word_name
                where user_id = :user_id
                and word_name = :word;""",
                {'user_id': user_id, 'word': word}
            ).fetchone()[0]
            SqlStatements._sql_logger.info(f'User count is: {count}')
        return count

    @staticmethod
    def get_highest_count_tuple():
        """get user with the highest count"""
        SqlStatements._sql_logger.debug('Get user with highest count')
        with SqlStatements._sqlite_connection:
            highest_count_tuple = SqlStatements._cursor.execute(
                "select * from users where count = (select max(count) from users)"
            ).fetchone()
        SqlStatements._sql_logger.debug(f'Got highest count: {highest_count_tuple}')
        return highest_count_tuple

    @staticmethod
    def insert_new_user(user_id):
        """insert new user into database"""
        with SqlStatements._sqlite_connection:
            SqlStatements._sql_logger.debug(f'Inserting new user {user_id}')
            SqlStatements._cursor.execute(
                "insert into user values (:user_id)",
                {'user_id': user_id}
            )
            SqlStatements._sql_logger.info(f'User {user_id} inserted to database')

    @staticmethod
    def check_user(user_id):
        # check if user is in database
        with SqlStatements._sqlite_connection:
            # get user_id
            SqlStatements._sql_logger.debug('Select user_id')
            SqlStatements._cursor.execute(
                "select id from user where id = :user_id",
                {'user_id': user_id}
            )
            SqlStatements._sql_logger.debug(f'User_id {user_id} selected')

        if SqlStatements._cursor.fetchall():
            # if user is already in database, return True
            SqlStatements._sql_logger.debug(f'User {user_id} is in database')
            return True
        else:
            SqlStatements._sql_logger.debug(f'User {user_id} not in database')
            return False

    @staticmethod
    def update_user_count(user_id, word, count):
        """Update user count"""
        SqlStatements._sql_logger.info('Updating count')
        with SqlStatements._sqlite_connection:
            # sum count
            current_count = SqlStatements.get_count(user_id)

            SqlStatements._cursor.execute(
                """update user set count = :count
                where user_id = :user_id
                and word_name = :word""",
                {'count': current_count + count, 'user_id': user_id, 'word': word}
            )
            SqlStatements._sql_logger.info(f'Updated count of user: {current_count + count}')
        SqlStatements._sql_logger.debug('Exiting insert_update_user_count')


if __name__ == '__main__':
    """testing for sql statements (will be replaced with unit testing (probably))"""
    # test setup
    SqlStatements.test()

    # get count test
    print(SqlStatements.get_count(372045873095639040, 'test'))
