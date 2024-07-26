import json, os, discord, logging, httpx, time, asyncio
from discord.ext import commands
from profanity_check import predict, predict_prob

from utlis.config import DISCORD_TOKEN, PROFANITY_THRESHOLD
from community_apps.discordHelper import (
    send_to_app, update_message, get_channels_and_messages, message_filter, available_commands,
    store_guild_info, store_channel_info, store_member_info, store_channel_list, get_parameters,
    profanity_checker
)
from backend.modelsPydantic import Message, UpdateChatHistory

class DiscordBot:
    def __init__(self, bot):
        self.bot = bot
        # Maintain a set of approved channels 
        self.approved_channels = set()  
        self.setup_bot()
        self.message_global = None

    def setup_bot(self):
        @self.bot.event
        async def on_ready():
            print(f'We have logged in as {self.bot.user}')

        @self.bot.event
        async def on_message(message):
            if message.author == self.bot.user:
                return

            if message.content:
                print(f"Direct content access: {message.content}")
                self.message_global = message       

                try:
                    profanity_scores = await profanity_checker([message.content])
                    profanity_score = profanity_scores[0]
                    
                    if profanity_score > PROFANITY_THRESHOLD:
                        try:
                            # remove and warn user if profanity score is high
                            await message.delete()
                            warning_message = f"{message.author.mention} your message is removed due to high profanity score: {int(profanity_score*100)}"
                            await message.channel.send(warning_message)

                        except Exception as e:
                            print(f"Error with deleting message: {e}")

                    if profanity_score > PROFANITY_THRESHOLD or await message_filter(message, self.bot.user):
                        message_info = await get_parameters(message)
                        asyncio.create_task(update_message(message_info, self.bot.user))

                except Exception as e:
                    print(f"Error with updating parameters: {e}")
                    response = None
            else:
                print("No content in message.content")

            if message.content.startswith('!invite'):
                await self.bot.process_commands(message)
            elif message.content.startswith('!'): 
                if message.channel.id not in self.approved_channels:
                    print("Received commands from an unapproved channel")
                    await message.channel.send("Invite bot with << !invite >> to use commands.")
                else:
                    print("Received commands from an approved channel")
                    await self.bot.process_commands(message)
            else:
                if message.channel.id in self.approved_channels:
                    print("Received message with no commands")
                else:
                    print("Received message from an unapproved channel")

        @self.bot.command(name='setup')
        async def setup(ctx):
            await self.update_server_info(ctx)

        @self.bot.command(name='info')
        async def info(ctx):
            await ctx.send(await available_commands())

        @self.bot.command(name='invite')
        async def invite(ctx):
            self.approved_channels.add(ctx.channel.id)
            await ctx.send(f"Bot invited to this channel: {ctx.channel.name}")
            await ctx.send(await available_commands())

        @self.bot.command(name='remove')
        async def remove(ctx):
            self.approved_channels.remove(ctx.channel.id)
            await ctx.send("Bot removed from this channel. \nType << !invite >> to add the bot back.")

        @self.bot.command(name='g')
        async def resource(ctx):
            await self.handle_query(ctx, 'resource_query')

        @self.bot.command(name='c')
        async def channel(ctx):
            await self.handle_query(ctx, 'channel_query')

    async def update_server_info(self, ctx):
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
            all_channels, all_messages = await get_channels_and_messages(guild, self.bot.user)
            await update_message(all_messages, self.bot.user)

            print(f"There are a total of {len(all_channels)} channels in {guild.name}")
            member_channels = {}
            total_messages = 0
            score_sum = 0 # sum of profanity scores * number of messages for each channel
            for channel in all_channels:
                channel_messages = all_messages[channel.id] 
                channel_info = await store_channel_info(channel, guild.id, channel_messages)
                await send_to_app('update_info', channel_info)

                # update total messages and score sum
                total_messages += channel_info['number_of_messages']
                score_sum += channel_info['profanity_score'] * channel_info['number_of_messages']

                # update member information
                print(f"There are a total of {len(channel.members)} members in {channel.name}")
                for member in channel.members:
                    if member not in member_channels:
                        member_channels[member] = []

                    member_info = await store_member_info(channel, member, channel_messages, guild.id)
                    
                    # record that the member is in this channel
                    if member_info:
                        member_channels[member].append(channel)
                        await send_to_app('update_info', member_info)

            await ctx.send("Channel and member information updated.")

            # update channel list for each member
            for member, channels in member_channels.items():
                print(f"Updating channel list for {member.name}")
                channel_list = await store_channel_list(member, guild, channels)
                await send_to_app('update_info', channel_list)

            # update guild information
            average_score = score_sum / total_messages if total_messages else 0
            guild_info = await store_guild_info(guild, average_score)
            await send_to_app('update_info', guild_info)

            print("Guild information updated.")
            await ctx.send("Guild information updated.")


        except Exception as e:
            print(f"Error with updating server information: {e}")
            await ctx.send("Failed to update server information.")

    async def handle_query(self, ctx, query_type):
        print(f"Received {query_type} command")
        print(f"Query: {self.message_global.content}")

        data = {
            'guild_id': ctx.guild.id,
            'channel_id': ctx.channel.id, 
            'query': self.message_global.content
        }

        await ctx.send("Processing query...")
        response = await send_to_app(query_type, data)

        if response.status_code == 200:
            # for channel query
            if isinstance(response.json().get('answer', {}), str):
                result = response.json().get('answer', {})
                sources = []
                
            # for resource query
            else:
                response_json = response.json()
                result = response_json.get('answer', {}).get('result', 'No result found')
                sources = response_json.get('answer', {}).get('sources', [])

            formatted_sources = '\n'.join([f"{source}" for source in sources])
            
            await ctx.send(self.message_global.author.mention)
            await ctx.send(result)
            if sources:
                await ctx.send(f"\nSources:\n{formatted_sources}")
        else:
            await ctx.send("Failed to get response from LLM.")