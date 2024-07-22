import os, json, httpx, discord

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

async def fetch_channel_messages(guild, bot_user, limit=100):
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
            async for message in discord_channel.history(limit=limit):
                if await message_filter(message, bot_user):
                    all_messages.append({
                        "channel_id": discord_channel.id,
                        "channel_name": discord_channel.name,
                        "message_id": message.id,
                        "author": message.author.name,
                        "content": message.content,
                        "timestamp": message.created_at.isoformat()
                    })

    return channels, all_messages

async def fetch_channel_info(guild):
    channels = [
        {
            "id": channel.id,
            "name": channel.name,
            "type": channel.type.name
        }
        for channel in guild.channels if isinstance(channel, discord.TextChannel)
    ]

    # 

async def message_filter(message, bot_user):
        # if message is a command and only a command
        if message.content.startswith('!'):
            print(f"Message is a command: {message.content}")
            return False
        
        # if message is too short, it's probably meaningless
        if len(message.content) < 10:
            print(f"Message is too short: {message.content}")
            return False

        # if message is for listing info
        if 'Available Commands:' in message.content:
            print(f"Message is a command list: {message.content}")
            return False
        
        # if message owner is the bot and less than 30 chars,
        if message.author == bot_user and len(message.content) < 30:
            print(f"Message is from bot and too short: {message.content}")
            return False
        
        # if none of the above conditions are met, return True
        return True


async def message_scanner():
    pass