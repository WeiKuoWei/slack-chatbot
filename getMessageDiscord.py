import json
import os
import fire
import discord
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("BEZOS_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

DATA_PATH = "data/discord/"
FILE_NAME = "messages"

class getMessage(discord.Client):
    async def on_ready(self):
        print(f'We have logged in as {self.user}')
        channel = self.get_channel(CHANNEL_ID)
        messages = await self.fetch_messages(channel)
        self.save_messages(messages, f'{FILE_NAME}.json')
        await self.close()

    async def fetch_messages(self, channel):
        messages = []
        async for message in channel.history(limit=None):
            messages.append({
                "id": message.id,
                "author": message.author.name,
                "content": message.content,
                "timestamp": message.created_at.isoformat()
            })
        return messages

    '''
    messages.append({
                "id": message.id,
                "author_id": message.author.id,
                "author_name": message.author.name,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
                "edited_at": message.edited_at.isoformat() if message.edited_at else None,
                "channel_id": message.channel.id,
                "guild_id": message.guild.id if message.guild else None,
                "attachments": [attachment.url for attachment in message.attachments],
                "embeds": [embed.to_dict() for embed in message.embeds],
                "reactions": [{"emoji": str(reaction.emoji), "count": reaction.count} for reaction in message.reactions],
                "mentions": [user.id for user in message.mentions],
                "mention_roles": [role.id for role in message.mention_roles],
                "mention_everyone": message.mention_everyone,
                "pinned": message.pinned,
                "type": str(message.type)
            })
    '''

    async def save_messages(self, messages, filename):
        os.makedirs(DATA_PATH, exist_ok=True)
        with open(f"{DATA_PATH}{filename}", 'w') as f:
            await json.dump(messages, f, indent=4)
        print(f'Saved {len(messages)} messages to {filename}')

class GetIds(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user}')
        for guild in self.guilds:
            print(f'Connected to guild: {guild.name}, ID: {guild.id}')
            for channel in guild.text_channels:
                print(f'Channel: {channel.name}, ID: {channel.id}')

        await self.close()
    
    async def on_message(self, message):
        if message.author == self.user:
            return
        
        if message.content.startswith('!serverid'):
            guild_id = message.guild.id
            await message.channel.send(f'This server ID is: {guild_id}')
        
        if message.content.startswith('!channelid'):
            channel_id = message.channel.id
            await message.channel.send(f'This channel ID is: {channel_id}')

# Define the intents
intents = discord.Intents.default()
intents.message_content = True

# Instantiate the getMessage client with intents
client = getMessage(intents=intents)
client.run(TOKEN)

# Instantiate the GetIds client with intents
client = GetIds(intents=intents)
client.run(TOKEN)
