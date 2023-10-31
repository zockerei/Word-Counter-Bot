import discord
import sqlite3
import logging.config
import yaml
import sql

# import logging_config
with open('logging_config.yaml', 'rt') as config_file:
    logging_config = yaml.safe_load(config_file.read())

sql_statements = sql.SqlStatements()

# logging setup
sql_statements.logging_setup(logging_config)
logging.config.dictConfig(logging_config)
discord_logger = logging.getLogger('discord')
bot_logger = logging.getLogger('bot.main')
bot_logger.debug('logging setup complete')


# intents
intents = discord.Intents.all()
client = discord.Client(intents=intents)

# load json
with open('bot_config.yaml') as config_file:
    bot_config = yaml.safe_load(config_file.read())
    token = bot_config['token']
    word = bot_config['word']
bot_logger.debug('bot_config loaded')


@client.event
async def on_ready():
    """Login and database setup"""
    bot_logger.info(f'Logged in as {client.user}')
    sql_statements.create_table()


@client.event
async def on_message(message):
    """Check message for the word and add it to the database"""
    if message.author == client.user:
        bot_logger.info('message is from author')
        return

    try:
        bot_logger.debug('setting up sql connection')
        message_content = message.content.lower()
        sqlite_connection = sqlite3.connect('users.db')
        cursor = sqlite_connection.cursor()

        if word not in message_content:
            bot_logger.info('word not found in message')
            return

        bot_logger.info('word found in message')
        count = message_content.count(word)
        user_id = message.author.id

        with sqlite_connection:
            bot_logger.debug('select user_id')
            cursor.execute("select user_id from users where user_id = :user_id",
                           {'user_id': user_id})

        if cursor.fetchall():
            """if user is already in database, sum count"""
            bot_logger.info('user is in database. Updating...')
            with sqlite_connection:
                bot_logger.debug('get count')
                current_count = cursor.execute("select count from users where user_id = :user_id",
                                               {'user_id': user_id}).fetchone()[0]

                bot_logger.debug('update count from user')
                cursor.execute("update users set count = :count where user_id = :user_id",
                               {'count': current_count + count, 'user_id': user_id})
        else:
            with sqlite_connection:
                bot_logger.info('inserting new user')
                cursor.execute("insert into users values (:user_id, :count)",
                               {'user_id': user_id, 'count': count})
    except sqlite3.Error as error:
        bot_logger.error(f'Working with Database failed {error}')
    else:
        if sqlite_connection:
            sqlite_connection.close()
            bot_logger.info('Connection to database closed')

client.run(token, log_handler=None)
