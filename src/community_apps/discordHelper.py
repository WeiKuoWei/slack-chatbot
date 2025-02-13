import os, json, httpx, discord
import numpy as np 
from profanity_check import predict_prob
from database.modelsChroma import (
    GuildInfo, ChannelInfo, MemberInfoChannel
)
from services.nlpTools import TextProcessor
from utlis.config import PROFANITY_THRESHOLD
from backend.modelsPydantic import UpdateChatHistory, Message

nlp_tools = TextProcessor()

async def send_to_app(route, data):
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(f'http://localhost:8000/{route}', json=data)
    return response

async def update_message(all_messages, bot_user, chunk_size=25):
    for channel_id, messages in all_messages.items():
        for chunk in chunk_list(messages, chunk_size):
            converted_message = {channel_id: [Message(**msg) for msg in chunk]}
            data = UpdateChatHistory(all_messages=converted_message)
            response = await send_to_app('update_chat_history', data.model_dump())

            if response.status_code == 200:
                print(f"Chunk of messages updated to ChromaDB for channel {channel_id}")
            else:
                print(f"Failed to update chunk of messages to ChromaDB for channel {channel_id}")

async def get_parameters(interaction_data):
    content = interaction_data["content"]
    author = interaction_data["author"]
    channel = interaction_data["channel"]
    guild = interaction_data["guild"]
    message_id = interaction_data["id"]
    created_at = interaction_data["created_at"]

    print(f"Updating message: {content}")
    data = {}

    profanity_scores = await profanity_checker([content]) # returns a numpy array
    print(f"Profanity score: {profanity_scores[0]}")
    message_info = {
        "channel_id": channel.id,
        "channel_name": channel.name,
        "message_id": message_id,
        "author": author.name,
        "author_id": author.id,
        "content": content,
        "timestamp": created_at.isoformat(),
        "profanity_score": profanity_scores[0]
    }

    data[channel.id] = [message_info]
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
                profanity_scores = await profanity_checker([message.content])
                profanity_score = profanity_scores[0]
                if profanity_score > PROFANITY_THRESHOLD or await message_filter(message, bot_user):
                    messages.append({
                        "channel_id": message.channel.id,
                        "channel_name": message.channel.name,
                        "message_id": message.id,
                        "author": message.author.name,
                        "author_id": message.author.id,
                        "content": message.content,
                        "timestamp": message.created_at.isoformat(),
                        "profanity_score": profanity_score
                    })
            all_messages[discord_channel.id] = messages

    return all_text_channels, all_messages

async def message_filter(message, bot_user): 
        # if message is a command and only a command
        if message.content.startswith('!') and len(message.content) < 10:
            return False
        
        # if message is too short, it's probably meaningless
        if len(message.content) < 10:
            return False

        # if message is for listing info
        if 'following commands' in message.content:
            return False

        # if message is a warning message
        if 'profanity score' in message.content:
            return False
        
        # if message owner is the bot and less than 50 chars,
        if message.author == bot_user and len(message.content) < 50:
            return False
        
        # if none of the above conditions are met, return True
        return True

async def available_commands():
    commands = (
        "Use / to view commands and interact with the Course Assistant:\n"
        "   1. /info - List available commands"
        "2. /channel - Queries related to channel\n"
        "3. /resource - Queries related to the course\n"
        "4. /setup - Use ONLY ONE time to setup chat history and server information. \n"
        "5. /load_course_materials - use ONLY ONE time to load course materials from course website\n"
        "6. /remove - Remove bot from channel\n"
    )
    return commands

# Calculate the profanity score of a message
async def profanity_checker(messages):
    contents = [message for message in messages]
    # save the content in a list; message should be a str
    for message in messages:
        contents.append(message)

    profanity_scores = predict_prob(contents) # numpy list
    # total_score = sum(profanity_scores)
    # average_score = total_score / len(messages) if messages else 0

    return profanity_scores

async def store_guild_info(guild, average_score):
    # store only the text channels
    channels = [
        channel for channel in guild.channels if isinstance(channel, discord.TextChannel)
    ]

    guild_info = {
        "guild_id": guild.id,
        "guild_name": guild.name,
        # "guild_purpose": "[placeholder]", # consider using guild.topic
        "number_of_channels": len(channels),
        "number_of_members": guild.member_count,
        "profanity_score": average_score
    }
    return guild_info

async def store_channel_info(channel, guild_id, messages):
    # profanity score is already stored in the message
    profanity_scores = np.array([msg['profanity_score'] for msg in messages])
    total_score = np.sum(profanity_scores)
    average_score = total_score / len(messages) if messages else 0

    # Extract content from messages
    message_contents = [msg['content'] for msg in messages]
    cleaned_documents, key_phrases, metadata, keywords = await nlp_tools.process_messages(message_contents)
    
    print(f"Cleaned documents: {cleaned_documents}\n Key phrases: {key_phrases}\n Metadata: {metadata}\n Keywords: {keywords}") 

    key_phrases_str = [' '.join(phrases) for phrases in key_phrases] 
    
    channel_info ={
        "channel_id": channel.id,
        "guild_id": guild_id,
        "channel_name": channel.name,
        "channel_purpose": str(key_phrases_str), 
        "number_of_messages": len(messages),
        "number_of_members": len(set([msg.get('author_id') for msg in messages])),
        "last_message_timestamp": messages[-1].get('timestamp') if messages else None,
        "first_message_timestamp": messages[0].get('timestamp') if messages else None,
        "profanity_score": average_score
    }

    return channel_info

async def store_member_info(channel, member, messages, guild_id):
    messages = [msg for msg in messages if msg["author_id"] == member.id]
    if messages == []:
        return None
    
    total_score = sum(msg['profanity_score'] for msg in messages)
    average_score = total_score / len(messages) if messages else 0

    member_info = {
        "user_id": member.id,
        "channel_id": channel.id,
        "channel_list_id": f"{guild_id}_{member.id}",
        "user_name": member.name,
        # "user_description": "[placeholder]",
        "message_sent": len(messages),
        "profanity_score": average_score
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


def chunk_list(data, chunk_size):
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]