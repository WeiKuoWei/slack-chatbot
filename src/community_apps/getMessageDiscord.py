# getMessageDiscord.py
import json, os, discord, requests, logging, httpx
from discord.ext import commands

from utlis.config import DISCORD_TOKEN


class DiscordBot:
    def __init__(self, bot):
        self.bot = bot
        self.setup_bot()

    def setup_bot(self):
        # Event: Bot is ready
        @self.bot.event
        async def on_ready():
            print(f'We have logged in as {self.bot.user}')

        # Event: Message received
        @self.bot.event
        async def on_message(message):
            logging.info(f"Message received: {message.content}")
            print(f"Message received: {message.content}")

            # Check if content is directly accessible
            if message.content:
                print(f"Direct content access: {message.content}")
            else:
                print("No content in message.content")


            # prevent bot from answering to itself
            if message.author == self.bot.user:
                return
            
            # Process commands
            await self.bot.process_commands(message)

            # Handle general messages
            if not message.content.startswith('!'):
                print(f"General message: {message.content}")

        # Command: Update chat history
        @self.bot.command(name='update')
        async def update(ctx):
            user = ctx.author
            guild = ctx.guild

            if not guild:
                print("This command can only be used in a server.")
                await ctx.send("This command can only be used in a server.")
                return
            else:
                print(f"Updating chat history for {guild.name}")
                await ctx.send("Updating chat history...")

            channels = [
                {
                    "id": channel.id,
                    "name": channel.name,
                    "type": channel.type.name
                }
                for channel in guild.channels if isinstance(channel, discord.TextChannel)
            ]

            all_messages = []
            for channel in channels:
                if channel['type'] == 'text':
                    discord_channel = guild.get_channel(channel['id'])
                    async for message in discord_channel.history(limit=100):
                        all_messages.append({
                            "channel_id": discord_channel.id,
                            "channel_name": discord_channel.name,
                            "message_id": message.id, # is a int in the data
                            "author": message.author.name,
                            "content": message.content,
                            "timestamp": message.created_at.isoformat()
                        })

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'http://localhost:8000/update',
                    json={'guild_id': guild.id, 'channels': channels, 'messages': all_messages}
                )

            if response.status_code == 200:
                await ctx.send("Update complete.")
            else:
                await ctx.send("Failed to update chat history.")

'''

if message.content.startswith('!ask'):
                query = message.content[len('!ask '):]
                response = requests.post('http://localhost:8000/query', json={'query': query, 'channel': message.channel.id})
                await message.channel.send(response.json()['answer'])

'''