import logging
from sqlalchemy.exc import SQLAlchemyError
from db.models import User, Word, UserHasWord
from typing import Optional, List, Tuple
from db.database import get_db

queries_logger = logging.getLogger('bot.queries')
queries_logger.info('Logging setup complete')


class DatabaseError(Exception):
    """
    Custom exception for database-related errors.

    Attributes:
        message (str): The error message.
        original_exception (Exception, optional): The original exception that caused this error.
    """

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        """
        Initializes the DatabaseError with a message and an optional original exception.

        Args:
            message (str): The error message.
            original_exception (Exception, optional): The original exception that caused this error.
        """
        self.message = message
        self.original_exception = original_exception
        super().__init__(self.message)


def drop_tables():
    """
    Drops tables from the database if they exist.

    Raises:
        DatabaseError: If there is an error dropping the tables.
    """
    try:
        with next(get_db()) as session:
            UserHasWord.__table__.drop(session.bind, checkfirst=True)
            Word.__table__.drop(session.bind, checkfirst=True)
            User.__table__.drop(session.bind, checkfirst=True)
            queries_logger.info('Tables dropped successfully')
    except SQLAlchemyError as e:
        queries_logger.error(f'Failed to drop tables: {e}')
        raise DatabaseError('Failed to drop tables', e)


def add_words(*words):
    """
    Adds words to the database if they don't exist.

    Args:
        *words: A variable number of word strings to add.

    Raises:
        DatabaseError: If there is an error inserting the words.
    """
    try:
        with next(get_db()) as session:
            for word in set(words):
                session.merge(Word(name=word))
            session.commit()
            queries_logger.info(f'Words added: {words}')
    except SQLAlchemyError as e:
        session.rollback()
        queries_logger.error(f'Error inserting words: {e}')
        raise DatabaseError('Error inserting words', e)


def add_user_ids(*user_ids):
    """
    Adds user IDs to the database if they don't exist.

    Args:
        *user_ids: A variable number of user ID integers to add.

    Raises:
        DatabaseError: If there is an error inserting the user IDs.
    """
    try:
        with next(get_db()) as session:
            for user_id in set(user_ids):
                session.merge(User(id=user_id, permission='user'))
            session.commit()
            queries_logger.info(f'User IDs added: {user_ids}')
    except SQLAlchemyError as e:
        session.rollback()
        queries_logger.error(f'Error inserting user IDs: {e}')
        raise DatabaseError('Error inserting user IDs', e)


def add_admins(*user_ids: int) -> None:
    """
    Adds admin permission to the specified user IDs.

    Args:
        *user_ids: A variable number of user ID integers to promote to admin.

    Raises:
        DatabaseError: If there is an error making users admin.
    """
    try:
        with next(get_db()) as session:
            for user_id in set(user_ids):
                user = session.query(User).filter_by(id=user_id).first()
                if user:
                    user.permission = 'admin'
            session.commit()
            queries_logger.info(f'Admins added: {user_ids}')
    except SQLAlchemyError as e:
        session.rollback()
        queries_logger.error(f'Failed to make users admin: {e}')
        raise DatabaseError('Failed to make users admin', e)


def add_user_has_word(user_id: int, word: str, count: int) -> None:
    """
    Inserts a new user_has_word record.

    Args:
        user_id (int): The ID of the user.
        word (str): The word associated with the user.
        count (int): The count of the word for the user.

    Raises:
        DatabaseError: If there is an error inserting the record.
    """
    try:
        with next(get_db()) as session:
            user_has_word = UserHasWord(user_id=user_id, word_name=word, count=count)
            session.merge(user_has_word)
            session.commit()
            queries_logger.info(f'Inserted user_has_word record: {user_id} | {word} | {count}')
    except SQLAlchemyError as e:
        session.rollback()
        queries_logger.error(f'Error inserting user_has_word record: {e}')
        raise DatabaseError('Error inserting user_has_word record', e)


def remove_word(word: str) -> None:
    """
    Removes a word from the database.

    Args:
        word (str): The word to remove.

    Raises:
        DatabaseError: If there is an error removing the word.
    """
    try:
        with next(get_db()) as session:
            word_obj = session.query(Word).filter_by(name=word).first()
            if word_obj:
                session.delete(word_obj)
                session.commit()
                queries_logger.info(f'Removed word: {word} successfully')
    except SQLAlchemyError as e:
        session.rollback()
        queries_logger.error(f'Error removing word: {e}')
        raise DatabaseError('Error removing word', e)


def get_count(user_id: int, word: str) -> Optional[int]:
    """
    Gets the count for a specific user ID and word.

    Args:
        user_id (int): The ID of the user.
        word (str): The word to get the count for.

    Returns:
        Optional[int]: The count of the word for the user, or None if not found.

    Raises:
        DatabaseError: If there is an error retrieving the count.
    """
    try:
        with next(get_db()) as session:
            user_has_word = session.query(UserHasWord).filter_by(user_id=user_id, word_name=word).first()
            result = user_has_word.count if user_has_word else None
            queries_logger.debug(f'get_count result for user {user_id}, word {word}: {result}')
            return result
    except SQLAlchemyError as e:
        queries_logger.error(f'Error getting count for user: {user_id} with word: {word}: {e}')
        raise DatabaseError('Error getting count', e)


def get_words() -> List[str]:
    """
    Gets all words from the database.

    Returns:
        List[str]: A list of all words in the database.

    Raises:
        DatabaseError: If there is an error retrieving the words.
    """
    try:
        with next(get_db()) as session:
            words = session.query(Word.name).all()
            result = [word.name for word in words]
            queries_logger.debug(f'get_words result: {result}')
            return result
    except SQLAlchemyError as e:
        queries_logger.error(f'Error retrieving words from the database: {e}')
        raise DatabaseError('Error retrieving words', e)


def get_all_users() -> List[int]:
    """
    Gets all user IDs from the database.

    Returns:
        List[int]: A list of all user IDs in the database.

    Raises:
        DatabaseError: If there is an error retrieving the user IDs.
    """
    try:
        with next(get_db()) as session:
            users = session.query(User.id).all()
            result = [user.id for user in users]
            queries_logger.debug(f'get_all_users result: {result}')
            return result
    except SQLAlchemyError as e:
        queries_logger.error(f'Error getting all users: {e}')
        raise DatabaseError('Error getting all users', e)


def get_highest_count_column(word: str) -> Optional[Tuple]:
    """
    Gets the user with the highest count for a specific word.

    Args:
        word (str): The word to find the highest count for.

    Returns:
        Optional[Tuple]: A tuple of (user_id, word_name, count) for the user with the highest count,
        or None if not found.

    Raises:
        DatabaseError: If there is an error retrieving the highest count.
    """
    try:
        with next(get_db()) as session:
            result = session.query(UserHasWord).filter_by(word_name=word).order_by(UserHasWord.count.desc()).first()
            tuple_result = (result.user_id, result.word_name, result.count) if result else None
            queries_logger.debug(f'get_highest_count_column result for word {word}: {tuple_result}')
            return tuple_result
    except SQLAlchemyError as e:
        queries_logger.error(f'Error while getting highest count for word {word}: {e}')
        raise DatabaseError('Error getting highest count', e)


def get_total_highest_count_column() -> Optional[Tuple]:
    """
    Gets the column with the highest count from the user_has_word table.

    Returns:
        Optional[Tuple]: A tuple of (user_id, word_name, count) for the highest count, or None if not found.

    Raises:
        DatabaseError: If there is an error retrieving the highest count column.
    """
    try:
        with next(get_db()) as session:
            result = session.query(UserHasWord).order_by(UserHasWord.count.desc()).first()
            tuple_result = (result.user_id, result.word_name, result.count) if result else None
            queries_logger.debug(f'get_total_highest_count_column result: {tuple_result}')
            return tuple_result
    except SQLAlchemyError as e:
        queries_logger.error(f'Error getting highest count column: {e}')
        raise DatabaseError('Error getting highest count column', e)


def update_user_count(user_id: int, word: str, count: int) -> None:
    """
    Updates the user count for a specific word.

    Args:
        user_id (int): The ID of the user.
        word (str): The word to update the count for.
        count (int): The count to add to the existing count.

    Raises:
        DatabaseError: If there is an error updating the count.
    """
    try:
        with next(get_db()) as session:
            user_has_word = session.query(UserHasWord).filter_by(user_id=user_id, word_name=word).first()
            if user_has_word:
                user_has_word.count += count
            else:
                user_has_word = UserHasWord(user_id=user_id, word_name=word, count=count)
                session.add(user_has_word)
            session.commit()
            queries_logger.info(f'Updated count for user: {user_id} with word: {word} to {count}')
    except SQLAlchemyError as e:
        session.rollback()
        queries_logger.error(f'Error updating count for user: {user_id} with word: {word}: {e}')
        raise DatabaseError('Error updating count', e)


def check_user_has_word(user_id: int, word: str) -> bool:
    """
    Checks if a user has an association with a specific word.

    Args:
        user_id (int): The ID of the user.
        word (str): The word to check association for.

    Returns:
        bool: True if the user has the word, False otherwise.

    Raises:
        DatabaseError: If there is an error checking the association.
    """
    try:
        with next(get_db()) as session:
            exists = session.query(UserHasWord).filter_by(user_id=user_id, word_name=word).first() is not None
            queries_logger.debug(f'check_user_has_word result for user {user_id}, word {word}: {exists}')
            return exists
    except SQLAlchemyError as e:
        queries_logger.error(f'Error in check_user_has_word: {e}')
        raise DatabaseError('Error checking user-word association', e)


def check_user_is_admin(user_id: int) -> bool:
    """
    Checks if a user has admin privileges.

    Args:
        user_id (int): The ID of the user.

    Returns:
        bool: True if the user is an admin, False otherwise.

    Raises:
        DatabaseError: If there is an error checking admin status.
    """
    try:
        with next(get_db()) as session:
            user = session.query(User).filter_by(id=user_id).first()
            result = user.permission == 'admin' if user else False
            queries_logger.debug(f'check_user_is_admin result for user {user_id}: {result}')
            return result
    except SQLAlchemyError as e:
        queries_logger.error(f'Error checking if user is admin: {e}')
        raise DatabaseError('Error checking admin status', e)


def get_user_word_counts(user_id: int) -> List[Tuple[str, int]]:
    """
    Gets all words and their counts for a specific user.

    Args:
        user_id (int): The ID of the user.

    Returns:
        List[Tuple[str, int]]: A list of tuples containing (word_name, count) for each word associated with the user.

    Raises:
        DatabaseError: If there is an error retrieving the user's word counts.
    """
    try:
        with next(get_db()) as session:
            results = session.query(UserHasWord).filter_by(user_id=user_id).all()
            result_list = [(result.word_name, result.count) for result in results]
            queries_logger.debug(f'get_user_word_counts result for user {user_id}: {result_list}')
            return result_list
    except SQLAlchemyError as e:
        queries_logger.error(f'Error retrieving words and counts for user: {user_id}: {e}')
        raise DatabaseError('Error retrieving user word counts', e)
