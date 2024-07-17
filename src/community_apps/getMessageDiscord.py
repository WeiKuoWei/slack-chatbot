# getMessageDiscord.py
import json, os, discord, logging, httpx, time
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
        self.message_global = None

    def setup_bot(self):
        # Event: Bot is ready
        @self.bot.event
        async def on_ready():
            print(f'We have logged in as {self.bot.user}')

        # Event: Message received
        '''
        messages should be sent to the database for storage
        '''

        @self.bot.event
        async def on_message(message):
            # prevent bot from answering to itself
            if message.author == self.bot.user:
                return
            
            else:
                # Check if content is directly accessible
                if message.content:
                    print(f"Direct content access: {message.content}")
                    self.message_global = message       

                    response = await self.update_parameters()   
                    if response.status_code == 200:
                        print("Message updated to ChromaDB")
                    else:
                        print("Failed to update message to ChromaDB")


                else:
                    print("No content in message.content")

            # EXCEPTION: Received bot invitation from user 
            if message.content.startswith('!invite'):
                await self.bot.process_commands(message)

            # For other commands
            elif message.content.startswith('!'): 
                if message.channel.id not in self.approved_channels:
                    print("Received commands from an unapproved channel")
                    await message.channel.send("Invite bot with << !invite >> to use commands.")
                    return
                
                else:
                    print("Received commands from an approved channel")
                    await self.bot.process_commands(message)
            
            else:
                if message.channel.id in self.approved_channels:
                    # Send to app and get gpt response if message is not a command
                    print("Received message with no commands")
                    response = await self.send_to_app(
                        'general', 
                        {'query': message.content, 'channel_id': message.channel.id, 'guild_id': message.guild.id}
                    )

                    if response.status_code == 200:
                        # if received response from LLM
                        if response.json()['answer']:
                            print("Receive LLM response from FastAPI")
                        await message.channel.send(response.json()['answer'])

                    else:
                        await message.channel.send("Failed to get response from LLM.")
                else:
                    print("Received message from an unapproved channel")

        # Command: Update chat history
        @self.bot.command(name='update')
        async def update(ctx):
            print("Updating chat history to ChromaDB...")
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
                print("Chat history updated.")
                await ctx.send("Chat history updated.")
                
            else:
                print("Failed to update chat history.")
                await ctx.send("Failed to update chat history.")

        # Command: Save the message to local # temporary use
        @self.bot.command(name='save')
        async def save(ctx):
            print("Saving messages...")

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

        # Command: Return a list of available commands
        @self.bot.command(name='info')
        async def info(ctx):
            print("Provide users with available commands")
                
            await ctx.send(
                "Available commands:\n"
                "!invite - Invite bot to channel\n"
                "!remove - Remove bot from channel\n"
                # "!channel - Query channel related information\n"
                # "!save - Save chat history to local\n"
                "!update - Update the entire ChromaDB with chat history (use once only) \n"
                "!info - List available commands"
            )
            '''
            update should be triggered upon invitation
            '''

        # Command: Invite bot to channel
        @self.bot.command(name='invite')
        async def invite(ctx):
            print(f"Bot invited to this channel: {ctx.channel.name}")

            self.approved_channels.add(ctx.channel.id)
            await ctx.send(f"Bot invited to this channel: {ctx.channel.name}")
            await ctx.send(
                "Available commands:\n"
                "!invite - Invite bot to channel\n"
                "!remove - Remove bot from channel\n"
                # "!channel - Query channel related information\n"
                # "!save - Save chat history to local\n"
                "!update - Update the entire ChromaDB with chat history (use once only) \n"
                "!info - List available commands"
            )

        # Command: Remove channel from approved list
        @self.bot.command(name='remove')
        async def remove(ctx):
            print(f"Bot removed from this channel: {ctx.channel.name}")

            self.approved_channels.remove(ctx.channel.id)
            await ctx.send(
                "Bot removed from this channel. \n" 
                "Type << !invite >> to add the bot back."
            )
            
        # Command: Respond to user with professor provided resources
        @self.bot.command(name='resource')
        async def resource(ctx):
            pass

        # Command: Respond to user with channel related query 
        @self.bot.command(name='channel')
        async def channel(ctx):
            print("Received channel command for channel related query")
            print(f"Query: {self.message_global.content} ")

            data = {
                'guild_id': ctx.guild.id,
                'channel_id': ctx.channel.id, 
                'query': self.message_global.content
            }

            response = await self.send_to_app('query_channel', data)
            if response.status_code == 200:
                await ctx.send(response.json()['answer'])
            else:
                await ctx.send("Failed to get response from LLM.")
    

    # ----------------- Helper Functions ----------------- # 

    async def send_to_app(self, route, data):
        async with httpx.AsyncClient(timeout = 60.0) as client:
            response = await client.post(
                f'http://localhost:8000/{route}',
                json=data
            )
        return response
    
    # Update user's response to ChromeDB
    async def update_parameters(self):
        # save message to database
        channel = {
            "id": self.message_global.channel.id,
            "name": self.message_global.channel.name,
            "type": self.message_global.channel.type.name
        }

        message_info = {
            "channel_id": self.message_global.channel.id,
            "channel_name": self.message_global.channel.name,
            "message_id": self.message_global.id,
            "author": self.message_global.author.name,
            "content": self.message_global.content,
            "timestamp": self.message_global.created_at.isoformat()
        }

        data = {
            "guild_id": self.message_global.guild.id,
            "channels": [channel],
            'messages': [message_info]
        }

        response = await self.send_to_app('update', data)
        return response

    # filter out meaningless messages
    async def message_filter(self, message):
        # if message is a command and only a command
        if message.content.startswith('!') and len(message.content) <= 1:
            return False

        # if message is for listing info
        if message.content.contains('Available Commands:'):
            return False
        
        # if message owner is the bot and less than 30 chars,
        
        # if none of the above conditions are met, return True
        return True


    # def split_message(message, max_length=1000):
    #     return [message[i:i + max_length] for i in range(0, len(message), max_length)]
