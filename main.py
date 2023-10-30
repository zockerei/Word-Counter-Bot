import discord
import sqlite3
import logging
import json

discord.utils.setup_logging()

# logger setup
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.INFO)
bot_logger = logging.getLogger('discord.bot')
bot_logger.setLevel(logging.DEBUG)

fileHandler = logging.FileHandler(filename='logger.log',
                                  encoding='utf-8',
                                  mode='w'
                                  )
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}',
                              '%Y-%m-%d %H:%M:%S',
                              style='{'
                              )
fileHandler.setFormatter(formatter)
logging.root.addHandler(fileHandler)

# intents
intents = discord.Intents.all()
client = discord.Client(intents=intents)

bot_logger.debug('loading json')
with open('config.json') as file:
    bot_logger.debug('file opened')
    data = json.load(file)
    token = data['Token']
    word = data['Word']


@client.event
async def on_ready():
    """Login and database setup"""
    bot_logger.info(f'Logged in as {client.user}')

    try:
        bot_logger.debug('setting up sql connection')
        sqlite_connection = sqlite3.connect('users.db')
        cursor = sqlite_connection.cursor()

        with sqlite_connection:
            bot_logger.debug('creating table if not exists')
            cursor.execute("""create table if not exists users (
                            user_id integer primary key,
                            count integer
                            )""")
    except sqlite3.Error as error:
        bot_logger.error(f'Connection to database failed: {error}')
    else:
        if sqlite_connection:
            sqlite_connection.close()
            bot_logger.info('Database ready and connection closed')


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
