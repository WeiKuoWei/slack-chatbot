import os, json, httpx, discord
from database.modelsChroma import (
    GuildInfo, ChannelInfo, MemberInfoChannel
)

from backend.modelsPydantic import UpdateChatHistory, Message

async def send_to_app(route, data):
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(f'http://localhost:8000/{route}', json=data)
    return response

async def update_message(message, bot_user):
    if await message_filter(message, bot_user):
        message = await get_parameters(message) 
        converted_message = {channel_id: [Message(**msg) for msg in messages] for channel_id, messages in message.items()}
        data = UpdateChatHistory(all_messages=converted_message)
        response = await send_to_app('update_chat_history', data.model_dump())
        
        if response.status_code == 200:
            print("Message updated to ChromaDB")
        else:
            print("Failed to update message to ChromaDB")

async def get_parameters(message):
    print(f"Updating message: {message.content}")
    data = {}
    message_info = {
        "channel_id": message.channel.id,
        "channel_name": message.channel.name,
        "message_id": message.id,
        "author": message.author.name,
        "author_id": message.author.id,
        "content": message.content,
        "timestamp": message.created_at.isoformat()
    }

    data[message.channel.id] = [message_info]
    return data

async def get_channels_and_messages(guild, bot_user, limit=500):
    channels = [
        {
            "id": channel.id,
            "name": channel.name,
            "type": channel.type.name
        }
        for channel in guild.channels if isinstance(channel, discord.TextChannel)
    ]

    all_messages = {}
    all_text_channels = []
    
    for channel in channels:
        if channel['type'] == 'text':
            discord_channel = guild.get_channel(channel['id'])
            all_text_channels.append(discord_channel)
            messages = []
            async for message in discord_channel.history(limit=limit):
                print(f"Checking message: {message.content}")
                if await message_filter(message, bot_user):
                    messages.append({
                        "channel_id": discord_channel.id,
                        "channel_name": discord_channel.name,
                        "message_id": message.id,
                        "author": message.author.name,
                        "author_id": message.author.id,
                        "content": message.content,
                        "timestamp": message.created_at.isoformat()
                    })
            all_messages[discord_channel.id] = messages

    return all_text_channels, all_messages

async def message_filter(message, bot_user):
        # if message is a command and only a command
        if message.content.startswith('!') and len(message.content) < 10:
            # print(f"Message is a command: {message.content}")
            return False
        
        # if message is too short, it's probably meaningless
        if len(message.content) < 10:
            # print(f"Message is too short: {message.content}")
            return False

        # if message is for listing info
        if 'following commands' in message.content:
            # print(f"Message is a command list: {message.content}")
            return False
        
        # if message owner is the bot and less than 50 chars,
        if message.author == bot_user and len(message.content) < 50:
            # print(f"Message is from bot and too short: {message.content}")
            return False
        
        # if none of the above conditions are met, return True
        print(f"Message is valid: {message.content}")
        return True

async def available_commands():
    commands = (
        "Use the following commands to interact with the TheRealJeffBezos:\n"
        "   1. !invite - Invite bot to channel\n"
        "2. !remove - Remove bot from channel\n"
        "3. !c - Query 'c'hannel related information\n"
        "4. !g - Query 'g'eneral information that are course related\n"
        "5. !setup - ONE time use; setup chat history and server information. \n"
        "6. !info - List available commands"
    )
    return commands

# Calculate the profanity score of a message
async def message_scanner():
    pass

async def store_guild_info(guild):
    guild_info = {
        "guild_id": guild.id,
        "guild_name": guild.name,
        # "guild_purpose": "[placeholder]", # consider using guild.topic
        "number_of_channels": len(guild.channels),
        "number_of_members": guild.member_count
    }
    '''
    guild.description is not added since it is not one of the attributes of the
    discord.Guild object. ChromaDB's page_content takes PyString as the type for
    page_content, and null cannot be converted to PyString.

    here, can also consider sending pydantic object instead of dict
    '''
    return guild_info

async def store_channel_info(channel, guild_id, messages):
    channel_info ={
        "channel_id": channel.id,
        "guild_id": guild_id,
        "channel_name": channel.name,
        # "channel_purpose": "[placeholder]", 
        "number_of_messages": len(messages),
        "number_of_members": len(set([msg.get('author_id') for msg in messages])),
        "last_message_timestamp": messages[-1].get('timestamp') if messages else None,
        "first_message_timestamp": messages[0].get('timestamp') if messages else None,
        # "profanity_score": 0 
    }

    return channel_info

async def store_member_info(channel, member, messages, guild_id):
    messages = [msg for msg in messages if msg["author_id"] == member.id]
    if messages == []:
        return None
    
    member_info = {
        "user_id": member.id,
        "channel_id": channel.id,
        "channel_list_id": f"{guild_id}_{member.id}",
        "user_name": member.name,
        # "user_description": "[placeholder]",
        "message_sent": len(messages),
        # "profanity_score": 0 
    }

    return member_info

async def store_channel_list(member, guild, channels):
    channel_ids = [channel.id for channel in channels]
    channel_list = {
        "user_id": member.id,
        "user_name": member.name,
        "guild_id": guild.id,
        "channel_ids": channel_ids
    }

    return channel_list
