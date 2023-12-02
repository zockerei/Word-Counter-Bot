import logging.config
import unittest
import yaml
import sql


class TestSqlModule(unittest.TestCase):
    _logger = None

    @classmethod
    def setUpClass(cls):
        # Loading logging config
        with open('logging_config.yaml', 'rt') as config_file:
            logging_config = yaml.safe_load(config_file.read())

        logging.config.dictConfig(logging_config)
        cls._logger = logging.getLogger('bot.unittest')
        cls._logger.debug('Logging config complete')

    def setUp(self):
        # Create sql_statements variable
        self.sql_statements = sql.SqlStatements()

        # Create tables
        self.sql_statements.create_tables()

    def tearDown(self):
        # Drop tables afterwards
        self.sql_statements.drop_tables()

    def testCreateTables(self):
        self._logger.debug("Testing creation of 'user' table")
        self.sql_statements.create_tables()

        # Check if 'user' table exists
        self._logger.debug('User table creation test')
        self.sql_statements.cursor.execute(
            """select name from sqlite_master
            where type='table' and name='user'"""
        )
        table_exists = self.sql_statements.cursor.fetchone() is not None
        self.assertTrue(
            table_exists,
            "The 'user' table does not exist"
        )
        self._logger.info('User table created successfully')

        # Check if 'user' table has expected columns
        self._logger.debug('User table columns test')
        self.sql_statements.cursor.execute("pragma table_info(user)")
        columns = [
            row[1]
            for row
            in self.sql_statements.cursor.fetchall()
        ]
        expected_columns = ['id']
        self.assertCountEqual(
            columns,
            expected_columns,
            "'user' table does not have an 'id' column"
        )
        self._logger.info("'user' table columns validated")

        # Check if 'word' table exists
        self._logger.debug('Word table creation test')
        self.sql_statements.cursor.execute(
            """select name from sqlite_master
            where type='table' and name='word'"""
        )
        table_exists = self.sql_statements.cursor.fetchone() is not None
        self.assertTrue(
            table_exists,
            "The 'word' table does not exist"
        )
        self._logger.info('Word table created successfully')

        # Check if 'word' table has expected columns
        self._logger.debug('Word table columns test')
        self.sql_statements.cursor.execute("pragma table_info(word)")
        columns = [
            row[1]
            for row
            in self.sql_statements.cursor.fetchall()
        ]
        expected_columns = ['name']
        self.assertCountEqual(
            columns,
            expected_columns,
            "'word' table does not have a 'name' column"
        )
        self._logger.info("'word' table columns validated")

        # Check if 'user_has_word' table exists
        self._logger.debug('User_has_word table creation test')
        self.sql_statements.cursor.execute(
            """select name from sqlite_master
            where type='table' and name='user_has_word'"""
        )
        table_exists = self.sql_statements.cursor.fetchone() is not None
        self.assertTrue(table_exists, "The 'user_has_word' table does not exist")
        self._logger.info('User_has_word table created successfully')

        # Check if 'user_has_word' table has expected columns
        self._logger.debug('User_has_word table columns test')
        self.sql_statements.cursor.execute("pragma table_info(user_has_word)")
        columns = [
            row[1]
            for row
            in self.sql_statements.cursor.fetchall()
        ]
        expected_columns = ['user_id', 'word_name', 'count']
        self.assertCountEqual(
            columns,
            expected_columns,
            "'user_has_word' table does not have the expected columns"
        )
        self._logger.info("'user_has_word' table columns validated")
        self._logger.debug("Finished createTables test")

    def testAddWords(self):
        self._logger.debug('Testing add_words method')

        words_to_add = ['word1', 'word2', 'word3']

        self._logger.debug('Calling add_words method')
        self.sql_statements.add_words(*words_to_add)

        # Verify that the words are added to the database
        self._logger.debug('Verifying words added to database')
        self.sql_statements.cursor.execute(
            """select * from word
            where name in (:word1, :word2, :word3)""",
            {'word1': words_to_add[0], 'word2': words_to_add[1], 'word3': words_to_add[2]}
        )

        added_words = [
            row[0]
            for row
            in self.sql_statements.cursor.fetchall()
        ]

        self.assertCountEqual(
            added_words,
            words_to_add,
            'Not all words were added to the database'
        )
        self._logger.info('add_words method tested successfully')

    def testAddUserIds(self):
        self._logger.debug('Testing add_guild_members method')

        # Define the guild members to add
        guild_members = {372045873095639040, 123456789012345678, 987654321098765432}

        # Call add_guild_members method
        self._logger.debug('Calling add_guild_members method')
        self.sql_statements.add_user_ids(*guild_members)

        # Verify that the users were added to the database
        added_users = self.sql_statements.get_all_users()

        self.assertSetEqual(set(added_users), guild_members, 'Not all users were added to the database')
        self._logger.info('add_guild_members method tested successfully')

    def testAddUserHasWord(self):
        self._logger.debug('Testing add_user_has_word method')

        # Input data for testing
        user_ids = [372045873095639040, 123456789012345678, 987654321098765432]
        words = ['word1', 'word2', 'word3']
        counts = [5, 6, 7]

        # Call the method
        self.sql_statements.add_user_has_word(user_ids, words, counts)

        # Verify the data is inserted correctly
        with sql.SqlStatements._sqlite_connection:
            result = sql.SqlStatements.cursor.execute("select * from user_has_word").fetchall()
        self._logger.debug(f'Result tuple is: {result}')

        # Check if the number of rows inserted matches the input data
        self.assertEqual(len(result), len(user_ids))
        self._logger.debug(f'Number of rows inserted: {len(result)}')

        # Check if the inserted data matches the input data
        for row, (expected_user_id, expected_word, expected_count)\
                in zip(result, zip(user_ids, words, counts)):
            self.assertEqual(row[0], expected_user_id)
            self.assertEqual(row[1], expected_word)
            self.assertEqual(row[2], expected_count)
            self._logger.debug(f"Row: {row[0]}, {row[1]}, {row[2]}")

    def testGetCount(self):
        self._logger.debug('Testing get_count method')

        # Add a user and a word to the database
        user_ids = [123456789012345678, 12345678912345678, 123456789123456789]
        words = ['test1', 'test2', 'test3']
        self.sql_statements.add_user_ids(*user_ids)
        self.sql_statements.add_words(*words)

        # Add counts for users and words
        counts_to_add = [5, 6, 7]
        self.sql_statements.add_user_has_word(user_ids, words, counts_to_add)

        # Call get_count method
        self._logger.debug('Calling get_count method')
        retrieved_counts = [
            self.sql_statements.get_count(user_id, word)
            for user_id, word
            in zip(user_ids, words)
        ]

        # Verify that the retrieved counts are correct
        self.assertListEqual(retrieved_counts, counts_to_add, 'Retrieved counts do not match expected counts')
        self._logger.info('get_count method tested successfully')

    def testGetWords(self):
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

    def testGetAllUsers(self):
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

    def testGetHighestCountColumn(self):
        self._logger.debug('Testing get_highest_count_column')

        # Input data for testing
        user_ids = [372045873095639040, 123456789012345678, 987654321098765432]
        word = 'word1'
        counts = [5, 8, 3]

        # Add user_has_word records for testing
        self.sql_statements.add_user_has_word(user_ids, [word] * len(user_ids), counts)

        # Call the method to get the highest count column for the specified word
        result = self.sql_statements.get_highest_count_column(word)

        # Check if the result is not None (indicating success)
        self.assertNotEqual(result, None)
        self._logger.debug(f'Result for {word}: {result}')

        # Check if the result is a tuple with the expected format (user_id, word, count)
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

    def testUpdateUserCount(self):
        self._logger.debug('Testing update_user_count method')

        # Input data for testing
        user_id = [372045873095639040]
        word = 'word1'
        count = [5]

        # Insert user, word, and count
        self.sql_statements.add_user_has_word(user_id, word, count)

        # Call the update method
        count[0] *= 2
        self.sql_statements.update_user_count(user_id, word, count)

        # Verify the data is updated correctly
        with sql.SqlStatements._sqlite_connection:
            result = sql.SqlStatements.cursor.execute(
                """select count from user_has_word
                where user_id = (:user_id)
                and word_name = (:word)""",
                {'user_id': user_id[0], 'word': word}
            ).fetchone()

        self.assertIsNotNone(result)
        updated_count = result[0]

        # Check if the count is updated correctly
        self.assertEqual(updated_count, count)
        self._logger.debug(f'Updated count: {updated_count}')


if __name__ == '__main__':
    unittest.main()