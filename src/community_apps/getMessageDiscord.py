# getMessageDiscord.py
import json, os, discord, requests, logging, httpx
from discord.ext import commands

from utlis.config import DISCORD_TOKEN


class DiscordBot:
    def __init__(self, bot):
        self.bot = bot
        # Maintain a set of approved channels 
        self.approved_channels = set()  
        '''
        will instead update the permission to allow the bot to read messages; bot should only response to uses if added to the channel
        '''
        self.setup_bot()

    def setup_bot(self):
        # Event: Bot is ready
        @self.bot.event
        async def on_ready():
            print(f'We have logged in as {self.bot.user}')

        # Event: Message received
        @self.bot.event
        async def on_message(message):
            # prevent bot from answering to itself
            if message.author == self.bot.user:
                return
            
            else:
                # Check if content is directly accessible
                if message.content:
                    print(f"Direct content access: {message.content}")
                else:
                    print("No content in message.content")

            # Process commands
            await self.bot.process_commands(message)

            # Check if message is from an approved channel
            if message.channel.id not in self.approved_channels:
                return

            # Send to app and get gpt response if message is not a command
            if not message.content.startswith('!'):
                response = await self.send_to_app('general', {'query': message.content, 'channel_id': message.channel.id})

                if response.status_code == 200:
                    # if received response from LLM
                    if response.json()['answer']:
                        print("Receive LLM response from FastAPI")
                    await message.channel.send(response.json()['answer'])

                else:
                    await message.channel.send("Failed to get response from LLM.")

        # Command: Update chat history
        @self.bot.command(name='update')
        async def update(ctx):
            # Check if message is from an approved channel
            if message.channel.id not in self.approved_channels:
                return

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
            
            data = {
                "guild_id": guild.id,
                "channels": channels,
                'messages': all_messages
            }

            response = await self.send_to_app('update', data)

            if response.status_code == 200:
                await ctx.send("Update complete.")
            else:
                await ctx.send("Failed to update chat history.")

        # save the message to local # temporary use
        @self.bot.command(name='save')
        async def save(ctx):
            # Check if message is from an approved channel
            if message.channel.id not in self.approved_channels:
                return
            
            guild_id = ctx.guild.id
            guild = ctx.guild

            channels = [
                {
                    "id": channel.id,
                    "name": channel.name,
                    "type": channel.type.name
                }
                for channel in guild.channels if isinstance(channel, discord.TextChannel)
            ]

            all_messages = {}
            for channel in channels:
                channel_messages = []
                if channel['type'] == 'text':
                    discord_channel = guild.get_channel(channel['id'])
                    async for message in discord_channel.history(limit=100):
                        channel_messages.append({
                            "guild_id": guild_id,
                            "channel_id": discord_channel.id,
                            "channel_name": discord_channel.name,
                            "message_id": message.id, # is an int in the data
                            "author": message.author.name,
                            "content": message.content,
                            "timestamp": message.created_at.isoformat()
                        })
                    
                    all_messages[channel["id"]] = channel_messages

            for channel_id, messages in all_messages.items():
                print(f"Saving messages for channel {channel_id}")
                dir_path = f"data/discord/{guild_id}/{channel_id}"
                os.makedirs(dir_path, exist_ok=True)
                file_path = os.path.join(dir_path, 'messages.json')
                with open(file_path, 'w') as f:
                    json.dump(messages, f, indent=4)

            await ctx.send("Messages saved.")
            print("Messages saved.")

        @self.bot.command(name='invite')
        async def invite(ctx):
            if ctx.channel.id not in self.approved_channels:
                self.approved_channels.add(ctx.channel.id)
                await ctx.send(f"Bot invited to this channel: {ctx.channel.name}")
            else:
                await ctx.send(f"Bot is already invited to this channel: {ctx.channel.name}")

        # Command: Remove channel from approved list
        @self.bot.command(name='remove')
        async def remove(ctx):
            if ctx.channel.id in self.approved_channels:
                self.approved_channels.remove(ctx.channel.id)
                await ctx.send(f"Bot removed from this channel: {ctx.channel.name}")
            else:
                await ctx.send(f"Bot was not in this channel: {ctx.channel.name}")

    async def send_to_app(self, route, data):
        async with httpx.AsyncClient(timeout = 60.0) as client:
            response = await client.post(
                f'http://localhost:8000/{route}',
                json=data
            )
        return response

    def split_message(message, max_length=1000):
        return [message[i:i + max_length] for i in range(0, len(message), max_length)]
