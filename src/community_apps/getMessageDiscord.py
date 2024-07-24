# getMessageDiscord.py
import json, os, discord, logging, httpx, time
from discord.ext import commands

from utlis.config import DISCORD_TOKEN
from community_apps.discordHelper import (
    send_to_app, update_parameters, get_channels_and_messages, message_filter, available_commands,
    store_guild_info, store_channel_info
    # , store_member_info, store_channel_list
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
                        if await message_filter(message, self.bot.user):
                            response = await update_parameters(message) 
                            
                            if response.status_code == 200:
                                print("Message updated to ChromaDB")
                            else:
                                print("Failed to update message to ChromaDB")
                        else:
                            print(f"Message {message.content} is not updated to ChromaDB")

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
            response = await send_to_app('update_chat_history', data.dict())
                
            if response.status_code == 200:
                print("Chat history updated.")
                await ctx.send("Chat history updated.")
                
            else:
                print("Failed to update chat history.")
                await ctx.send("Failed to update chat history.")

        # Command: update server information, including guild_info,
        # channel_info, member_info, etc.
        @self.bot.command(name='setup')
        async def setup(ctx):
            print("Updating server information to ChromaDB...")
            guild = ctx.guild

            if not guild:
                print("This command can only be used in a server.")
                await ctx.send("This command can only be used in a server.")
                return
            else:
                print(f"Updating server information for {guild.name}")
                await ctx.send("Updating server information...")

            # # store server information to ChromaDB
            # guild_info = await store_guild_info(guild)
            # response = await send_to_app('update_guild_info', guild_info)

            text_channels, messages = await get_channels_and_messages(guild, self.bot.user)

            # for channel in guild.channels:
            #     if isinstance(channel, discord.TextChannel):
                    
            #         print(f"Updating channel information for {channel.name}")
            #         await store_channel_info(channel, guild.id)

                    # for member in channel.members:
                    #     await store_member_info(channel, member)
                    #     await store_channel_list(member, guild)

            await ctx.send("Server information updated.")

            # if response.status_code == 200:
            #     print("Server information updated.")
            #     await ctx.send("Server information updated.")
                
            # else:
            #     print("Failed to update server information.")
            #     await ctx.send("Failed to update server information.")

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
