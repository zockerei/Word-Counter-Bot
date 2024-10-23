import unittest
import logging
from config.config import setup_logging
import src.sql as sql


class TestSqlModule(unittest.TestCase):
    _logger = None

    @classmethod
    def setUpClass(cls):
        # Use the setup_logging function from config
        setup_logging()
        cls._logger = logging.getLogger('bot.unittest')
        cls._logger.info('Logging config complete')

    def setUp(self):
        # Initialize SQL statements and create tables
        self.sql_statements = sql.SqlStatements()
        self.sql_statements.create_tables()

    def tearDown(self):
        # Drop tables after each test
        self.sql_statements.drop_tables()

    def test_create_tables(self):
        self._logger.debug("Testing creation of 'user' table")
        self.sql_statements.create_tables()

        # Check if 'user' table exists
        self._logger.debug('User table creation test')
        result = self.sql_statements._execute_query(
            """SELECT name FROM sqlite_master
            WHERE type='table' AND name='user'""",
            fetch_one=True
        )
        table_exists = result is not None
        self.assertTrue(table_exists, "The 'user' table does not exist")
        self._logger.info('User table created successfully')

        # Check if 'user' table has expected columns
        self._logger.debug('User table columns test')
        result = self.sql_statements._execute_query("PRAGMA table_info(user)")
        columns = [row[1] for row in result]
        expected_columns = ['id', 'permission']
        self.assertCountEqual(
            columns,
            expected_columns,
            "'user' table does not have the expected columns"
        )
        self._logger.info("'user' table columns validated")

        # Check if 'word' table exists
        self._logger.debug('Word table creation test')
        result = self.sql_statements._execute_query(
            """SELECT name FROM sqlite_master
            WHERE type='table' AND name='word'""",
            fetch_one=True
        )
        table_exists = result is not None
        self.assertTrue(table_exists, "The 'word' table does not exist")
        self._logger.info('Word table created successfully')

        # Check if 'word' table has expected columns
        self._logger.debug('Word table columns test')
        result = self.sql_statements._execute_query("PRAGMA table_info(word)")
        columns = [row[1] for row in result]
        expected_columns = ['name']
        self.assertCountEqual(
            columns,
            expected_columns,
            "'word' table does not have a 'name' column"
        )
        self._logger.info("'word' table columns validated")

        # Check if 'user_has_word' table exists
        self._logger.debug('User_has_word table creation test')
        result = self.sql_statements._execute_query(
            """SELECT name FROM sqlite_master
            WHERE type='table' AND name='user_has_word'""",
            fetch_one=True
        )
        table_exists = result is not None
        self.assertTrue(table_exists, "The 'user_has_word' table does not exist")
        self._logger.info('User_has_word table created successfully')

        # Check if 'user_has_word' table has expected columns
        self._logger.debug('User_has_word table columns test')
        result = self.sql_statements._execute_query("PRAGMA table_info(user_has_word)")
        columns = [row[1] for row in result]
        expected_columns = ['user_id', 'word_name', 'count']
        self.assertCountEqual(
            columns,
            expected_columns,
            "'user_has_word' table does not have the expected columns"
        )
        self._logger.info("'user_has_word' table columns validated")

        # Check foreign key constraints
        self._logger.debug('Foreign key constraints test')
        result = self.sql_statements._execute_query("PRAGMA foreign_key_list(user_has_word)")
        foreign_keys = [row[3] for row in result]
        expected_foreign_keys = ['user_id', 'word_name']
        self.assertCountEqual(
            foreign_keys,
            expected_foreign_keys,
            "'user_has_word' table does not have the expected foreign key constraints"
        )
        self._logger.info("Foreign key constraints validated")
        self._logger.debug("Finished createTables test")

    def test_add_words(self):
        self._logger.debug('Testing add_words method')

        words_to_add = ['word1', 'word2', 'word3']

        self._logger.debug('Calling add_words method')
        self.sql_statements.add_words(*words_to_add)

        # Verify that the words are added to the database
        self._logger.debug('Verifying words added to database')
        result = self.sql_statements._execute_query(
            """select * from word
            where name in (:word1, :word2, :word3)""",
            params={'word1': words_to_add[0], 'word2': words_to_add[1], 'word3': words_to_add[2]}
        )

        added_words = [row[0] for row in result]

        self.assertCountEqual(
            added_words,
            words_to_add,
            'Not all words were added to the database'
        )
        self._logger.info('add_words method tested successfully')

    def test_add_user_ids(self):
        self._logger.debug('Testing add_user_ids method')  # Updated method name

        # Define the user IDs to add
        user_ids = {372045873095639040, 123456789012345678, 987654321098765432}

        # Call add_user_ids method
        self._logger.debug('Calling add_user_ids method')  # Updated method name
        self.sql_statements.add_user_ids(*user_ids)

        # Verify that the users were added to the database
        added_users = self.sql_statements.get_all_users()

        self.assertSetEqual(set(added_users), user_ids, 'Not all users were added to the database')
        self._logger.info('add_user_ids method tested successfully')  # Updated method name

    def test_add_admin(self):
        self._logger.debug('Testing add_admins method')  # Updated method name

        # Test adding admin to an existing user (success case)
        user_id_existing_user = 1
        self._logger.debug(f"Inserting user {user_id_existing_user} with permission 'user' into the database")
        self.sql_statements._execute_query(
            "INSERT INTO user (id, permission) VALUES (:user_id, :permission)",
            params={'user_id': user_id_existing_user, 'permission': 'user'}
        )

        # Call the add_admins method
        self._logger.debug(f"Calling add_admins method for user {user_id_existing_user}")  # Updated method name
        self.sql_statements.add_admins(user_id_existing_user)  # Updated method name

        # Check if the user is now an admin in the database
        result_existing_user = self.sql_statements._execute_query(
            "SELECT permission FROM user WHERE id = :user_id",
            params={'user_id': user_id_existing_user},
            fetch_one=True
        )
        self.assertEqual(
            result_existing_user[0], 'admin',
            f"User {user_id_existing_user} is not an admin"
        )

        # Test adding admin to an existing admin (success case)
        user_id_existing_admin = 2
        self._logger.debug(f"Inserting admin {user_id_existing_admin} with permission 'admin' into the database")
        self.sql_statements._execute_query(
            "INSERT INTO user (id, permission) VALUES (:user_id, :permission)",
            params={'user_id': user_id_existing_admin, 'permission': 'admin'}
        )

        # Call the add_admins method
        self._logger.debug(f"Calling add_admins method for admin {user_id_existing_admin}")  # Updated method name
        self.sql_statements.add_admins(user_id_existing_admin)  # Updated method name

        # Check if the admin's permission is still 'admin' in the database
        result_existing_admin = self.sql_statements._execute_query(
            "SELECT permission FROM user WHERE id = :user_id",
            params={'user_id': user_id_existing_admin},
            fetch_one=True
        )
        self.assertEqual(
            result_existing_admin[0], 'admin',
            f"User {user_id_existing_admin} is not an admin"
        )

        self._logger.info('add_admin method tested successfully')

    def test_add_user_has_word(self):
        self._logger.debug('Testing add_user_has_word method')

        # Input data for testing
        user_ids = [372045873095639040, 123456789012345678, 987654321098765432]
        words = ['word1', 'word2', 'word3']
        counts = [5, 6, 7]

        # Iterate over the input data and call the method
        for user_id, word, count in zip(user_ids, words, counts):
            self.sql_statements.add_user_has_word(user_id, word, count)

        # Verify the data is inserted correctly using the existing method
        result = self.sql_statements._execute_query(
            "SELECT * FROM user_has_word",
            'Fetched user_has_word records successfully',
            'Error fetching user_has_word records'
        )
        self._logger.debug(f'Result tuple is: {result}')

        # Check if the number of rows inserted matches the input data
        self.assertEqual(len(result), len(user_ids))
        self._logger.debug(f'Number of rows inserted: {len(result)}')

        # Check if the inserted data matches the input data
        for row, (expected_user_id, expected_word, expected_count) in zip(result, zip(user_ids, words, counts)):
            self.assertEqual(row[0], expected_user_id)
            self.assertEqual(row[1], expected_word)
            self.assertEqual(row[2], expected_count)
            self._logger.debug(f"Row: {row[0]}, {row[1]}, {row[2]}")

    def test_remove_word(self):
        self._logger.debug('Testing remove_word method')

        # Set up initial data or conditions needed for the test
        initial_word = 'TestWord'
        self._logger.debug(f"Inserting word '{initial_word}' into the database")
        self.sql_statements._execute_query(
            "insert into word (name) values (:word);",
            'Inserted test word successfully',
            'Error inserting test word',
            {'word': initial_word}
        )

        # Call the method you want to test
        removed_word = 'TestWord'
        self._logger.debug(f"Calling remove_word method for word '{removed_word}'")
        self.sql_statements.remove_word(removed_word)

        # Perform assertions to check if the word was removed successfully
        query = "select count(*) from word where name = :word;"
        count = self.sql_statements._execute_query(
            query,
            'Counted occurrences of word successfully',
            'Error counting occurrences of word',
            {'word': removed_word},
            True
        )
        self.assertEqual(count[0], 0, f"The word '{removed_word}' still exists in the database.")

        self._logger.info('remove_word method tested successfully')

    def test_get_count(self):
        self._logger.debug('Testing get_count method')

        # Add a user and a word to the database
        user_ids = [123456789012345678, 12345678912345678, 123456789123456789]
        words = ['test1', 'test2', 'test3']
        counts = [5, 6, 7]
        self.sql_statements.add_user_ids(*user_ids)
        self.sql_statements.add_words(*words)

        # Iterate over the input data and call the method
        for user_id, word, count in zip(user_ids, words, counts):
            self.sql_statements.add_user_has_word(user_id, word, count)

        # Call get_count method with non-existing user and word
        non_existing_user_id = 987654321012345678
        non_existing_word = 'non_existing_word'
        non_existing_count = self.sql_statements.get_count(non_existing_user_id, non_existing_word)

        # Verify that the count for non-existing user and word is None
        self.assertIsNone(
            non_existing_count,
            'Count for non-existing user and word should be None'
        )

        # Call get_count method for existing user and word
        self._logger.debug('Calling get_count method')
        retrieved_counts = [
            self.sql_statements.get_count(user_id, word)
            for user_id, word
            in zip(user_ids, words)
        ]

        # Verify that the retrieved counts are correct
        for retrieved_count, expected_count in zip(retrieved_counts, counts):
            self.assertEqual(
                retrieved_count,
                expected_count,
                'Retrieved counts do not match expected counts'
            )

        self._logger.info('get_count method tested successfully')

    def test_get_words(self):
        self._logger.debug('Testing get_words method')

        # Insert some words into the database for testing
        test_words = ['word1', 'word2', 'word3']
        self.sql_statements.add_words(*test_words)

        # Call the get_words method
        self._logger.debug('Calling get_words method')
        retrieved_words = self.sql_statements.get_words()

        # Verify that the retrieved words match the inserted words
        self.assertCountEqual(
            retrieved_words,
            test_words,
            'Retrieved words do not match inserted words'
        )
        self._logger.info('get_words method tested successfully')

    def test_get_all_users(self):
        self._logger.debug('Testing get_all_users')

        # Define user IDs to add
        user_ids_to_add = [372045873095639040, 123456789012345678, 987654321098765432]

        # Add user IDs to the database
        self.sql_statements.add_user_ids(*user_ids_to_add)

        # Call get_all_users to retrieve user IDs from the database
        retrieved_user_ids = self.sql_statements.get_all_users()

        # Verify that the retrieved user IDs match the ones added
        self.assertSetEqual(
            set(retrieved_user_ids),
            set(user_ids_to_add),
            'Retrieved user IDs do not match the added ones'
        )

        self._logger.info('get_all_users method tested successfully')

    def test_get_highest_count_column(self):
        self._logger.debug('Testing get_highest_count_column')

        # Input data for testing
        user_ids = [372045873095639040, 123456789012345678, 987654321098765432]
        word = 'word1'
        counts = [5, 8, 3]

        # Iterate over the input data and call the method
        for user_id, word, count in zip(user_ids, [word] * len(user_ids), counts):
            self.sql_statements.add_user_has_word(user_id, word, count)

        # Call the method to get the highest count column for the specified word
        result = self.sql_statements.get_highest_count_column(word)

        # Check if the result is not None (indicating success)
        self.assertNotEqual(result, None)
        self._logger.debug(f'Result for {word}: {result}')

        # Check if the result is a tuple with the expected format (user_id, word_name, count)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        self._logger.debug(f'Result format for {word} is as expected')

        # Check if the result matches the expected data
        expected_user_id = user_ids[counts.index(max(counts))]  # Get the user with the highest count
        expected_word = word
        expected_count = max(counts)
        self.assertEqual(result[0], expected_user_id)
        self.assertEqual(result[1], expected_word)
        self.assertEqual(result[2], expected_count)
        self._logger.debug(f"Result for {word} matches the expected data")

    def test_update_user_count(self):
        self._logger.debug('Testing update_user_count method')

        # Input data for testing
        user_id = 372045873095639040
        word = 'word1'
        initial_count = 5

        # Insert user, word, and initial count
        self.sql_statements.add_user_ids(user_id)
        self.sql_statements.add_words(word)
        self.sql_statements.add_user_has_word(user_id, word, initial_count)

        # Call the update method to add 5 more to the count
        self.sql_statements.update_user_count(user_id, word, 5)

        # Verify the data is updated correctly
        result = self.sql_statements.get_count(user_id, word)  # Use get_count method to verify

        self.assertIsNotNone(result)

        # Check if the count is updated correctly
        self.assertEqual(result, 10)
        self._logger.debug(f'Updated count: {result}')

    def test_check_user_has_word(self):
        self._logger.debug('Testing check_user_has_word method')

        # Add a user and a word to the database
        user_id = 123456789012345678
        word = 'testword'
        count = 1
        self.sql_statements.add_user_ids(user_id)
        self.sql_statements.add_words(word)
        self.sql_statements.add_user_has_word(user_id, word, count)

        # Check if the user has the word
        has_word = self.sql_statements.check_user_has_word(user_id, word)
        self.assertTrue(has_word, f"User {user_id} should have the word '{word}'")

        # Check for a word the user does not have
        non_existing_word = 'nonexistentword'
        has_word = self.sql_statements.check_user_has_word(user_id, non_existing_word)
        self.assertFalse(has_word, f"User {user_id} should not have the word '{non_existing_word}'")

        self._logger.info('check_user_has_word method tested successfully')

    def test_check_user_is_admin(self):
        self._logger.debug('Testing check_user_is_admin method')

        # Add a user with admin permission
        user_id = 123456789012345678
        self.sql_statements.add_user_ids(user_id)
        self.sql_statements.add_admins(user_id)

        # Check if the user is an admin
        is_admin = self.sql_statements.check_user_is_admin(user_id)
        self.assertTrue(is_admin, f"User {user_id} should be an admin")

        # Add a user without admin permission
        non_admin_user_id = 987654321098765432
        self.sql_statements.add_user_ids(non_admin_user_id)

        # Check if the user is not an admin
        is_admin = self.sql_statements.check_user_is_admin(non_admin_user_id)
        self.assertFalse(is_admin, f"User {non_admin_user_id} should not be an admin")

        self._logger.info('check_user_is_admin method tested successfully')

    def test_get_total_highest_count_column(self):
        self._logger.debug('Testing get_total_highest_count_column method')

        # Input data for testing
        user_ids = [372045873095639040, 123456789012345678, 987654321098765432]
        words = ['word1', 'word2', 'word3']
        counts = [5, 8, 3]

        # Add data to the database
        for user_id, word, count in zip(user_ids, words, counts):
            self.sql_statements.add_user_has_word(user_id, word, count)

        # Get the total highest count column
        result = self.sql_statements.get_total_highest_count_column()

        # Check if the result is not None
        self.assertIsNotNone(result, "The result should not be None")

        # Check if the result matches the expected data
        expected_user_id = user_ids[counts.index(max(counts))]
        expected_word = words[counts.index(max(counts))]
        expected_count = max(counts)
        self.assertEqual(result[0], expected_user_id)
        self.assertEqual(result[1], expected_word)
        self.assertEqual(result[2], expected_count)

        self._logger.info('get_total_highest_count_column method tested successfully')

    def test_get_user_word_counts(self):
        self._logger.debug('Testing get_user_word_counts method')

        # Input data for testing
        user_id = 123456789012345678
        words = ['word1', 'word2', 'word3']
        counts = [5, 6, 7]

        # Add data to the database
        self.sql_statements.add_user_ids(user_id)
        self.sql_statements.add_words(*words)
        for word, count in zip(words, counts):
            self.sql_statements.add_user_has_word(user_id, word, count)

        # Get the user's word counts
        result = self.sql_statements.get_user_word_counts(user_id)

        # Check if the result matches the expected data
        expected_result = list(zip(words, counts))
        self.assertCountEqual(result, expected_result, "The user's word counts do not match the expected data")

        self._logger.info('get_user_word_counts method tested successfully')


if __name__ == '__main__':
    unittest.main()
