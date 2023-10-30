import discord
import sqlite3
import json

intents = discord.Intents.all()
client = discord.Client(intents=intents)

with open('config.json') as file:
    data = json.load(file)
    token = data['Token']
    word = data['Word']


@client.event
async def on_ready():
    """Login and setup database"""
    print(f'Logged in as {client.user}')

    try:
        sqlite_connection = sqlite3.connect('users.db')
        cursor = sqlite_connection.cursor()

        with sqlite_connection:
            cursor.execute("""create table if not exists users (
                            user_id integer primary key,
                            count integer
                            )""")
        print('Database ready')
    except sqlite3.Error as error:
        print(f'Connection to database failed: {error}')
    else:
        if sqlite_connection:
            sqlite_connection.close()
            print('Connection closed')


@client.event
async def on_message(message):
    """Check message for the word and add it to the database"""
    if message.author == client.user:
        return

    try:
        message_content = message.content.lower()
        sqlite_connection = sqlite3.connect('users.db')
        cursor = sqlite_connection.cursor()

        if word not in message_content:
            return

        count = message_content.count(word)
        user_id = message.author.id
        with sqlite_connection:
            cursor.execute("select user_id from users where user_id = :user_id",
                           {'user_id': user_id})

        if cursor.fetchall():
            """if user is already in database, sum count"""
            with sqlite_connection:
                current_count = cursor.execute("select count from users where user_id = :user_id",
                                               {'user_id': user_id}).fetchone()[0]

                cursor.execute("update users set count = :count",
                               {'count': current_count + count})
        else:
            with sqlite_connection:
                cursor.execute("insert into users values (:user_id, :count)",
                               {'user_id': user_id, 'count': count})
    except sqlite3.Error as error:
        print(f'Connection to Database failed {error}')
    else:
        if sqlite_connection:
            sqlite_connection.close()
            print('Connection closed')

client.run(token)
