# modelsChroma.py
import asyncio
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings

async def generate_embedding(text):
    embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")
    return embedding_model.embed_query(text)

'''
consider using text-embedding-3-large as an embedding alternative
'''

class ChatHistory:
    def __init__(self, data):
        # id 
        self.message_id = data['message_id']
        
        # document
        self.content = data['content']

        # metadata
        self.channel_name = data['channel_name']
        self.author = data['author']
        self.timestamp = data['timestamp']

    async def to_document(self):
        embedding = await generate_embedding(self.content)
        return Document(
            page_content=self.content, 
            metadata={
                'channel_name': self.channel_name,
                'id': self.message_id,
                'author': self.author,
                'timestamp': self.timestamp
            }
        ), embedding
    
    '''
    reactions is not added since it is a list; metadata has to be either
    type str, int, float, or bool to be added to the document
    '''
    

'''
For each class, will need to decide what the metadata will be and what the
document will be. At the moment, team_ids and team_id don't seem to have
metadata

'''