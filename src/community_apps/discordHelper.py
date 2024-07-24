import os, json, httpx, discord
from database.modelsChroma import (
    GuildInfo, ChannelInfo
)

async def send_to_app(route, data):
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(f'http://localhost:8000/{route}', json=data)
    return response

async def update_parameters(message):
    print(f"Updating message: {message.content}")
    channel = {
        "id": message.channel.id,
        "name": message.channel.name,
        "type": message.channel.type.name
    }

    message_info = {
        "channel_id": message.channel.id,
        "channel_name": message.channel.name,
        "message_id": message.id,
        "author": message.author.name,
        "content": message.content,
        "timestamp": message.created_at.isoformat()
    }

    data = {
        "guild_id": message.guild.id,
        "channels": [channel],
        'messages': [message_info]
    }

    response = await send_to_app('update', data)
    return response

async def get_channels_and_messages(guild, bot_user, limit=100):
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
                if await message_filter(message, bot_user):
                    messages.append({
                        "channel_id": discord_channel.id,
                        "channel_name": discord_channel.name,
                        "message_id": message.id,
                        "author": message.author.name,
                        "content": message.content,
                        "timestamp": message.created_at.isoformat()
                    })
            all_messages[discord_channel.id] = messages

    return all_text_channels, all_messages

async def message_filter(message, bot_user):
        # if message is a command and only a command
        if message.content.startswith('!') and len(message.content) < 10:
            print(f"Message is a command: {message.content}")
            return False
        
        # if message is too short, it's probably meaningless
        if len(message.content) < 10:
            print(f"Message is too short: {message.content}")
            return False

        # if message is for listing info
        if 'Available commands:' in message.content:
            print(f"Message is a command list: {message.content}")
            return False
        
        # if message owner is the bot and less than 50 chars,
        if message.author == bot_user and len(message.content) < 50:
            print(f"Message is from bot and too short: {message.content}")
            return False
        
        # if none of the above conditions are met, return True
        return True

async def available_commands():
    commands = (
        "Use the following commands to interact with the TheRealJeffBezos:\n"
        "   1. !invite - Invite bot to channel\n"
        "2. !remove - Remove bot from channel\n"
        "3. !c - Query 'c'hannel related information\n"
        "4. !g - Query 'g'eneral information that are course related\n"
        "5. !update - Update the entire ChromaDB with chat history (use once only)\n"
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
        "number_of_channels": len(guild.channels),
        "number_of_members": guild.member_count
    }
    '''
    guild.description is not added since it is not one of the attributes of the
    discord.Guild object. ChromaDB's page_content takes PyString as the type for
    page_content, and null cannot be converted to PyString.
    '''
    return guild_info

async def store_channel_info(channel, guild_id):
    messages = await channel.history(limit=None).flatten()
    try:
        channel_info = ChannelInfo({
            "channel_id": channel.id,
            "guild_id": guild_id,
            "channel_nme": channel.name,
            "channel_purpose": channel.topic,
            "number_of_messages": len(messages),
            "number_of_members": len(channel.members),
            "last_message_timestamp": messages[-1].created_at.isoformat() if messages else None,
            "first_message_timestamp": messages[0].created_at.isoformat() if messages else None,
            "profanity_score": 0  # Calculate this based on your criteria
        })
    except Exception as e:
        print(f"Error with channel info: {e}")

    try:
        dir_path = f"data/discord/{guild_id}/{channel.id}"
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, 'channel_info.json')

        with open(file_path, 'w') as f:
            json.dump(channel_info.__dict__, f, indent=4)
    except Exception as e:
        print(f"Error with saving channel info: {e}")

# async def store_member_info(channel, member):
#     messages = [msg async for msg in channel.history(limit=None) if msg.author.id == member.id]
#     member_info = MemberInfoChannel({
#         "user_id": member.id,
#         "channel_id": channel.id,
#         "user_name": member.name,
#         "user_description": member.nick,
#         "message_sent": len(messages),
#         "profanity_score": 0  # Calculate this based on your criteria
#     })

#     dir_path = f"data/discord/{channel.guild.id}/{channel.id}/{member.id}"
#     os.makedirs(dir_path, exist_ok=True)
#     file_path = os.path.join(dir_path, 'member_info.json')

#     with open(file_path, 'w') as f:
#         json.dump(member_info.__dict__, f, indent=4)

# async def store_channel_list(member, guild):
#     channel_list = [channel.id for channel in guild.channels if member in channel.members]
#     channel_list_data = {
#         "channel_list_id": f"{guild.id}_{member.id}",
#         "channel_id": channel_list
#     }

#     dir_path = f"data/discord/{guild.id}/{member.id}"
#     os.makedirs(dir_path, exist_ok=True)
#     file_path = os.path.join(dir_path, 'channel_list.json')

#     with open(file_path, 'w') as f:
#         json.dump(channel_list_data, f, indent=4)
