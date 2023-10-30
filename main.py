import discord
import os
from dotenv import load_dotenv

load_dotenv()
intents = discord.Intents.all()
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

client.run(os.getenv('TOKEN'))
