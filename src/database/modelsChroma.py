# modelsChroma.py
import asyncio
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings

# embedding model options
async def generate_embedding(text, option = "openai"):
    if option == "openai":
        embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")
    else:
        embedding_model = SentenceTransformerEmbeddings(model="all-MiniLM-L6-v2")
    
    return embedding_model.embed_query(text)

'''
1. Consider using text-embedding-3-large as an embedding alternative
2. Note that metadata has to be either type str, int, float, or bool to be added to the document
'''

# Store the general information for a guild (server)
# collection name: guild_info
class GuildInfo:
    def __init__(self, data):
        self.guild_id = data['guild_id']
        self.guild_name = data['guild_name']   
        self.guild_purpose = data.get('guild_purpose', 'null')
        self.number_of_channels = data['number_of_channels']
        self.number_of_members = data['number_of_members']
        self.profanity_score = data.get('profanity_score', 0)

    async def to_document(self):
        embedding = await generate_embedding(self.guild_purpose)
        return Document(
            page_content=self.guild_purpose, 
            metadata={
                'id': self.guild_id, # id
                'guild_name': self.guild_name,
                'number_of_channels': self.number_of_channels,
                'number_of_members': self.number_of_members
            }
        ), embedding

# Store the general information for a channel
# collection name: channel_info_{guild_id}
class ChannelInfo:
    def __init__(self, data):
        self.channel_id = data['channel_id']
        self.guild_id = data['guild_id']
        self.channel_name = data['channel_name']
        self.channel_purpose = data.get('channel_purpose', '')
        self.number_of_messages = data['number_of_messages']
        self.number_of_members = data['number_of_members']
        self.last_message_timestamp = data['last_message_timestamp']
        self.first_message_timestamp = data['first_message_timestamp']
        self.profanity_score = data.get('profanity_score', 0)

    async def to_document(self):
        embedding = await generate_embedding(self.channel_purpose)
        return Document(
            page_content=self.channel_purpose, 
            metadata={
                'id': self.channel_id, # id
                'guild_id': self.guild_id,
                'channel_name': self.channel_name,
                'number_of_messages': self.number_of_messages,
                'number_of_members': self.number_of_members,
                'last_message_timestamp': self.last_message_timestamp,
                'first_message_timestamp': self.first_message_timestamp,
                'profanity_score': self.profanity_score
            }
        ), embedding

# Store the general information for a member in a channel
# collection name: member_info_{channel_id}
class MemberInfoChannel:
    def __init__(self, data):
        self.user_id = data['user_id']
        self.channel_id = data['channel_id']
        self.channel_list_id = data['channel_list_id']
        self.user_name = data['user_name']
        self.user_description = data.get('user_description', '')
        self.message_sent = data['message_sent']
        self.profanity_score = data.get('profanity_score', 0)

    async def to_document(self):
        embedding = await generate_embedding(self.user_description)
        return Document(
            page_content=self.user_description, 
            metadata={
                'id': self.user_id,
                'channel_id': self.channel_id,
                'channel_list_id': self.channel_list_id,
                'user_name': self.user_name,
                'message_sent': self.message_sent,
                'profanity_score': self.profanity_score
            }
        ), embedding


# Store the list of channels a member is in, links to ChannelInfo
# collection name: channel_list_{guild_id}
class ChannelList:
    def __init__(self, data):
        self.user_id = data['user_id']   
        self.user_name = data['user_name']
        self.guild_id = data['guild_id']
        self.channel_ids = data['channel_ids']

    async def to_document(self):
        # convert list to string
        content = str(self.user_id) + "_" + self.user_name
        embedding = await generate_embedding(content)
        return Document(
            page_content= content, 
            metadata={
                'id': self.user_id,
                'user_name': self.user_name,
                'guild_id': self.guild_id,
                'channel_ids': str(self.channel_ids)
            }
        ), embedding

# Stores the chat history for each channel id
# collection name: chat_history_{channel_id}
class ChatHistory:
    def __init__(self, data):
        self.message_id = data['message_id']
        self.content = data['content']
        self.channel_name = data['channel_name']
        self.author = data['author']
        self.author_id = data['author_id']
        self.timestamp = data['timestamp']

    async def to_document(self):
        embedding = await generate_embedding(self.content)
        return Document(
            page_content=self.content, 
            metadata={
                'id': self.message_id,
                'channel_name': self.channel_name,
                'author': self.author,
                'timestamp': self.timestamp
            }
        ), embedding
