import unittest
import logging
from config import setup_logging
from db import queries


class TestQueries(unittest.TestCase):
    """
    Test suite for database query operations.

    This class contains tests for all database operations defined in the queries module.
    Each test method follows the pattern of setting up test data, performing operations,
    and verifying results.

    Attributes:
        test_logger: Logger instance for test-specific logging.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up class-level fixtures.
        This method is called once before running all tests in the class.
        """
        setup_logging()
        cls.test_logger = logging.getLogger('tests.queries')
        cls.test_logger.info('Test logging configuration complete')

    def setUp(self):
        """
        Set up test fixtures.
        This method is called before each test method.
        """
        self.test_logger.info('Setting up test environment')
        queries.drop_tables()
        self.test_logger.debug('Tables dropped successfully')

    def tearDown(self):
        """
        Clean up test fixtures.
        This method is called after each test method.
        """
        self.test_logger.info('Cleaning up test environment')
        queries.drop_tables()
        self.test_logger.debug('Tables dropped successfully')

    def test_add_words(self):
        """
        Test adding words to the database.

        Tests:
            - Words can be successfully added to the database
            - All added words can be retrieved
            - No duplicate words are created
        """
        self.test_logger.info('Starting test_add_words')
        words_to_add = ['word1', 'word2', 'word3']

        queries.add_words(*words_to_add)
        added_words = queries.get_words()

        self.assertCountEqual(added_words, words_to_add, 'Not all words were added to the database')
        self.test_logger.info('Completed test_add_words')

    def test_add_user_ids(self):
        """
        Test adding user IDs to the database.

        Tests:
            - User IDs can be successfully added to the database
            - All added user IDs can be retrieved
            - No duplicate user IDs are created
        """
        self.test_logger.info('Starting test_add_user_ids')
        user_ids = {372045873095639040, 123456789012345678, 987654321098765432}

        queries.add_user_ids(*user_ids)
        added_users = queries.get_all_users()

        self.assertSetEqual(set(added_users), user_ids, 'Not all user IDs were added to the database')
        self.test_logger.info('Completed test_add_user_ids')

    def test_add_admins(self):
        """
        Test adding admin privileges to users.

        Tests:
            - Regular users can be promoted to admin status
            - Admin status is correctly reflected in the database
            - Non-admin users remain unchanged
        """
        self.test_logger.info('Starting test_add_admins')
        user_id = 123456789012345678

        queries.add_user_ids(user_id)
        queries.add_admins(user_id)
        is_admin = queries.check_user_is_admin(user_id)

        self.assertTrue(is_admin, f"User {user_id} should be an admin")
        self.test_logger.info('Completed test_add_admins')

    def test_add_user_has_word(self):
        """
        Test associating words with users and their counts.

        Tests:
            - Words can be associated with users
            - Count values are correctly stored
            - Associations can be retrieved accurately
        """
        self.test_logger.info('Starting test_add_user_has_word')
        user_id = 123456789012345678
        word = 'testword'
        count = 5

        queries.add_user_ids(user_id)
        queries.add_words(word)
        queries.add_user_has_word(user_id, word, count)

        result_count = queries.get_count(user_id, word)
        self.assertEqual(result_count, count, 'Count does not match expected value')
        self.test_logger.info('Completed test_add_user_has_word')

    def test_remove_word(self):
        """
        Test removing words from the database.

        Tests:
            - Words can be successfully removed
            - Removed words are no longer retrievable
            - Database remains consistent after removal
        """
        self.test_logger.info('Starting test_remove_word')
        word = 'TestWord'

        queries.add_words(word)
        queries.remove_word(word)

        words = queries.get_words()
        self.assertNotIn(word, words, f"The word '{word}' still exists in the database.")
        self.test_logger.info('Completed test_remove_word')

    def test_get_count(self):
        """
        Test retrieving word counts for user-word pairs.

        Tests:
            - Correct counts are retrieved for existing user-word pairs
            - None is returned for non-existing pairs
            - Multiple user-word pairs maintain separate counts
        """
        self.test_logger.info('Starting test_get_count')
        user_ids = [123456789012345678, 987654321098765432]
        words = ['test1', 'test2']
        counts = [5, 6]

        queries.add_user_ids(*user_ids)
        queries.add_words(*words)

        for user_id, word, count in zip(user_ids, words, counts):
            queries.add_user_has_word(user_id, word, count)

        non_existing_count = queries.get_count(999999999, 'nonexistent')
        self.assertIsNone(non_existing_count)

        for user_id, word, expected_count in zip(user_ids, words, counts):
            count = queries.get_count(user_id, word)
            self.assertEqual(count, expected_count)

        self.test_logger.info('Completed test_get_count')

    def test_get_words(self):
        """
        Test retrieving all words from the database.

        Tests:
            - All added words can be retrieved
            - Retrieved words match the original input
            - Word order is not significant
        """
        self.test_logger.info('Starting test_get_words')
        test_words = ['word1', 'word2', 'word3']

        queries.add_words(*test_words)
        retrieved_words = queries.get_words()

        self.assertCountEqual(retrieved_words, test_words)
        self.test_logger.info('Completed test_get_words')

    def test_get_all_users(self):
        """
        Test retrieving all users from the database.

        Tests:
            - All added users can be retrieved
            - Retrieved user IDs match the original input
            - User ID order is not significant
        """
        self.test_logger.info('Starting test_get_all_users')
        user_ids = [372045873095639040, 123456789012345678, 987654321098765432]

        queries.add_user_ids(*user_ids)
        retrieved_users = queries.get_all_users()

        self.assertSetEqual(set(retrieved_users), set(user_ids))
        self.test_logger.info('Completed test_get_all_users')

    def test_get_highest_count_column(self):
        """
        Test retrieving the highest count for a specific word.

        Tests:
            - Correctly identifies the user with the highest count
            - Returns correct word and count values
            - Handles multiple users with different counts
        """
        self.test_logger.info('Starting test_get_highest_count_column')
        user_ids = [372045873095639040, 123456789012345678]
        word = 'testword'
        counts = [5, 8]

        queries.add_user_ids(*user_ids)
        queries.add_words(word)

        for user_id, count in zip(user_ids, counts):
            queries.add_user_has_word(user_id, word, count)

        result = queries.get_highest_count_column(word)
        expected = (user_ids[1], word, counts[1])

        self.assertEqual(result, expected)
        self.test_logger.info('Completed test_get_highest_count_column')

    def test_update_user_count(self):
        """
        Test updating word counts for users.

        Tests:
            - Counts can be incremented correctly
            - Updates are persistent
            - Original count plus increment equals new count
        """
        self.test_logger.info('Starting test_update_user_count')
        user_id = 372045873095639040
        word = 'word1'
        initial_count = 5
        increment = 5

        queries.add_user_ids(user_id)
        queries.add_words(word)
        queries.add_user_has_word(user_id, word, initial_count)
        queries.update_user_count(user_id, word, increment)

        new_count = queries.get_count(user_id, word)
        self.assertEqual(new_count, initial_count + increment)
        self.test_logger.info('Completed test_update_user_count')

    def test_check_user_has_word(self):
        """
        Test checking if a user has a specific word.

        Tests:
            - Returns True for existing user-word pairs
            - Returns False for non-existing pairs
            - Correctly handles different users with same words
        """
        self.test_logger.info('Starting test_check_user_has_word')
        user_id = 123456789012345678
        word = 'testword'

        queries.add_user_ids(user_id)
        queries.add_words(word)
        queries.add_user_has_word(user_id, word, 1)

        has_word = queries.check_user_has_word(user_id, word)
        self.assertTrue(has_word)

        has_word = queries.check_user_has_word(user_id, 'nonexistent')
        self.assertFalse(has_word)
        self.test_logger.info('Completed test_check_user_has_word')

    def test_check_user_is_admin(self):
        """
        Test checking user admin status.

        Tests:
            - Returns True for admin users
            - Returns False for non-admin users
            - Correctly differentiates between admin and non-admin users
        """
        self.test_logger.info('Starting test_check_user_is_admin')
        admin_id = 123456789012345678
        non_admin_id = 987654321098765432

        queries.add_user_ids(admin_id, non_admin_id)
        queries.add_admins(admin_id)

        self.assertTrue(queries.check_user_is_admin(admin_id))
        self.assertFalse(queries.check_user_is_admin(non_admin_id))
        self.test_logger.info('Completed test_check_user_is_admin')

    def test_get_total_highest_count_column(self):
        """
        Test retrieving the highest count across all words.

        Tests:
            - Correctly identifies the highest count among all words
            - Returns correct user, word, and count values
            - Handles multiple users and words with different counts
        """
        self.test_logger.info('Starting test_get_total_highest_count_column')
        user_ids = [372045873095639040, 123456789012345678]
        words = ['word1', 'word2']
        counts = [5, 8]

        queries.add_user_ids(*user_ids)
        queries.add_words(*words)

        for user_id, word, count in zip(user_ids, words, counts):
            queries.add_user_has_word(user_id, word, count)

        result = queries.get_total_highest_count_column()
        expected = (user_ids[1], words[1], counts[1])

        self.assertEqual(result, expected)
        self.test_logger.info('Completed test_get_total_highest_count_column')

    def test_get_user_word_counts(self):
        """
        Test retrieving word counts for a specific user.

        Tests:
            - Multiple word-count associations can be created for a user
            - Correct word-count pairs are retrieved
            - Results maintain the expected format of (word, count) tuples
        """
        self.test_logger.info('Starting test_get_user_word_counts')
        user_id = 123456789012345678
        words = ['word1', 'word2', 'word3']
        counts = [5, 6, 7]

        queries.add_user_ids(user_id)
        queries.add_words(*words)

        for word, count in zip(words, counts):
            queries.add_user_has_word(user_id, word, count)

        result = queries.get_user_word_counts(user_id)
        expected_result = list(zip(words, counts))

        self.assertCountEqual(result, expected_result)
        self.test_logger.info('Completed test_get_user_word_counts')


if __name__ == '__main__':
    unittest.main()
