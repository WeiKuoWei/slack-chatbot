from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from transformers import AutoTokenizer, AutoModel
import torch

embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")

def generate_embedding(text):
    return embedding_model.embed_query(text)

class Channel_info:
    def __init__(self, data):
        # id
        self.message_id = data['id']
        
        # document
        self.message = data['message']

        # metadata
        self.person = data['person']
        self.datetime = data['datetime']
        self.reactions = data['reactions']
        self.replies = data['replies']

    def to_document(self):
        embedding = generate_embedding(self.message)
        return Document(
            page_content=self.message, 
            metadata={
            'id': self.message_id,
            'person': self.person,
            'datetime': self.datetime,
            # 'reactions': self.reactions, 
            'replies': self.replies
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