# getMessageDiscord.py
import json, os, discord, logging, httpx, time, asyncio
from discord.ext import commands

from utlis.config import DISCORD_TOKEN
from community_apps.discordHelper import (
    send_to_app, update_message, get_channels_and_messages, message_filter, available_commands,
    store_guild_info, store_channel_info, store_member_info, store_channel_list
)

from backend.modelsPydantic import Message, UpdateChatHistory

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

                    try:
                        asyncio.create_task(update_message(message, self.bot.user))

                    except Exception as e:
                        print(f"Error with updating parameters: {e}")
                        response = None
                      
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
                    
                else:
                    print("Received message from an unapproved channel")

        # Command: Update chat history
        @self.bot.command(name='update')
        async def update(ctx):
            print("Updating chat history to ChromaDB...")
            guild = ctx.guild

            if not guild:
                print("This command can only be used in a server.")
                await ctx.send("This command can only be used in a server.")
                return
            else:
                print(f"Updating chat history for {guild.name}")
                await ctx.send("Updating chat history...")

            # get channel and channel messages
            try:
                _, all_messages = await get_channels_and_messages(guild, self.bot.user)

            except Exception as e:
                print(f"Error with fetching channel messages: {e}")
                all_messages = {}

            # here, update_chat_history takes an instance of Dict[int,
            # List[Message]]. Message is a Pydantic model, thus all_messages will need to be
            # converted manually into a list of Message instances
            converted_messages = {channel_id: [Message(**msg) for msg in messages] for channel_id, messages in all_messages.items()}
            data = UpdateChatHistory(all_messages=converted_messages)
            print("Messages converted to Pydantic model.")
            response = await send_to_app('update_chat_history', data.model_dump())
                
            if response.status_code == 200:
                print("Chat history updated.")
                await ctx.send("Chat history updated.")
                
            else:
                print("Failed to update chat history.")
                await ctx.send("Failed to update chat history.")

        # Command: update chat history server information, including guild_info,
        # channel_info, member_info, etc.
        @self.bot.command(name='setup')
        async def setup(ctx):
            print("Updating server information and chat history to ChromaDB...")
            guild = ctx.guild

            if not guild:
                print("This command can only be used in a server.")
                await ctx.send("This command can only be used in a server.")
                return
            else:
                print(f"Updating server information for {guild.name}")
                await ctx.send("Updating server information...")

            try:
                # get all channels and messages from the server
                all_channels, all_messages = await get_channels_and_messages(guild, self.bot.user)
                
                # add all messages to ChromaDB
                converted_messages = {channel_id: [Message(**msg) for msg in messages] for channel_id, messages in all_messages.items()}
                data = UpdateChatHistory(all_messages=converted_messages)
                await send_to_app('update_chat_history', data.model_dump())

                # store server information to ChromaDB
                guild_info = await store_guild_info(guild)
                await send_to_app('update_info', guild_info)

                # save channel, member, and channel list information to the database
                print(f"There are a total of {len(all_channels)} channels in {guild.name}")
                member_channels = {}
                for channel in all_channels:
                    # get the messages for this specific channel
                    channel_messages = all_messages[channel.id] 
                    channel_info = await store_channel_info(channel, guild.id, channel_messages)
                    await send_to_app('update_info', channel_info)

                    print(f"There are a total of {len(channel.members)} members in {channel.name}")
                    for member in channel.members:
                        if member not in member_channels:
                            member_channels[member] = []
                        member_info = await store_member_info(channel, member, channel_messages, guild.id)
                    
                        # check if member is in this channel; if not, member_info will be None
                        if member_info:
                            member_channels[member].append(channel)
                            await send_to_app('update_info', member_info)
                
                for member, channels in member_channels.items():
                    print(f"Updating channel list for {member.name}")
                    channel_list = await store_channel_list(member, guild, channels)
                    await send_to_app('update_info', channel_list)

                print("Server information updated.")
                await ctx.send("Server information updated.")

            except Exception as e:
                print(f"Error with updating server information: {e}")
                await ctx.send("Failed to update server information.")
                
                '''
                at the moment, storing member info in guild level is not
                implemented instead, guild level info will be calculated
                based on channel level info a channel_list collection will
                be created to store the list of channels a member is in, and
                it will be used to compose guild level info
                
                however, will need to figure out a way to dynamically update
                channel level member info and channel list will a new member
                is added to a channel
                '''
        # Command: Return a list of available commands
        @self.bot.command(name='info')
        async def info(ctx):
            print("Provide users with available commands")
                
            await ctx.send(await available_commands())

        # Command: Invite bot to channel
        @self.bot.command(name='invite')
        async def invite(ctx):
            print(f"Bot invited to this channel: {ctx.channel.name}")

            self.approved_channels.add(ctx.channel.id)
            await ctx.send(f"Bot invited to this channel: {ctx.channel.name}")
            await ctx.send(await available_commands())

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
        @self.bot.command(name='g')
        async def resource(ctx):
            print("Received resource command for professor provided resources")
            print(f"Query: {self.message_global.content}")

            data = {
                'guild_id': ctx.guild.id,
                'channel_id': ctx.channel.id, 
                'query': self.message_global.content
            }

            response = await send_to_app('resource_query', data)
            print(f"Response: {response.json()['answer']['result']}")
            print(f"Sources: {response.json()['answer']['sources']}")
            if response.status_code == 200:
                await ctx.send(response.json()['answer']['result'])
                await ctx.send(f"Sources: {response.json()['answer']['sources']}")

            else:
                await ctx.send("Failed to get response from LLM.")

        # Command: Respond to user with channel related query 
        @self.bot.command(name='c')
        async def channel(ctx):
            print("Received channel command for channel related query")
            print(f"Query: {self.message_global.content}")

            data = {
                'guild_id': ctx.guild.id,
                'channel_id': ctx.channel.id, 
                'query': self.message_global.content
            }

            response = await send_to_app('channel_query', data)
            if response.status_code == 200:
                await ctx.send(response.json()['answer'])
            else:
                await ctx.send("Failed to get response from LLM.")
