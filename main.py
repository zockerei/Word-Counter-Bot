import discord
import sqlite3
import logging
import json

# logger setup
logging.basicConfig(filename='logger.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                    )
handler = logging.FileHandler(filename='logger.log',
                              encoding='utf-8'
                              )

# intents
intents = discord.Intents.all()
client = discord.Client(intents=intents)

logging.info('loading json')
with open('config.json') as file:
    logging.debug('file opened')
    data = json.load(file)
    token = data['Token']
    word = data['Word']


@client.event
async def on_ready():
    """Login and setup database"""
    logging.info(f'Logged in as {client.user}')

    try:
        logging.debug('setting up sql connection')
        sqlite_connection = sqlite3.connect('users.db')
        cursor = sqlite_connection.cursor()

        with sqlite_connection:
            logging.debug('creating table if not exists')
            cursor.execute("""create table if not exists users (
                            user_id integer primary key,
                            count integer
                            )""")
        logging.info('Database ready')
    except sqlite3.Error as error:
        logging.error(f'Connection to database failed: {error}')
    else:
        if sqlite_connection:
            sqlite_connection.close()
            logging.info('Connection closed')


@client.event
async def on_message(message):
    """Check message for the word and add it to the database"""
    if message.author == client.user:
        logging.info('message is from author')
        return

    try:
        logging.debug('setting up sql connection')
        message_content = message.content.lower()
        sqlite_connection = sqlite3.connect('users.db')
        cursor = sqlite_connection.cursor()

        if word not in message_content:
            logging.info('word not found in message')
            return

        logging.info('word found in message')
        count = message_content.count(word)
        user_id = message.author.id

        with sqlite_connection:
            logging.debug('select user_id')
            cursor.execute("select user_id from users where user_id = :user_id",
                           {'user_id': user_id})

        if cursor.fetchall():
            """if user is already in database, sum count"""
            logging.info('user is in database. Updating...')
            with sqlite_connection:
                logging.debug('get count')
                current_count = cursor.execute("select count from users where user_id = :user_id",
                                               {'user_id': user_id}).fetchone()[0]

                logging.debug('update count from user')
                cursor.execute("update users set count = :count",
                               {'count': current_count + count})
        else:
            with sqlite_connection:
                logging.info('inserting new user')
                cursor.execute("insert into users values (:user_id, :count)",
                               {'user_id': user_id, 'count': count})
    except sqlite3.Error as error:
        logging.error(f'Working with Database failed {error}')
    else:
        if sqlite_connection:
            sqlite_connection.close()
            logging.info('Connection closed')

client.run(token, log_handler=handler)
