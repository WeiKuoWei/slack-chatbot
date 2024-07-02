from langchain.schema import Document
from transformers import AutoTokenizer, AutoModel
import torch

# Load pre-trained model and tokenizer from Hugging Face
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

def generate_embedding(text):
    inputs = tokenizer(text, return_tensors='pt', padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().tolist()

class Team_ids:
    def __init__(self, team_id, name_of_workspace, number_of_channels, number_of_members):
        # id
        self.team_id = team_id
        
        # metadata
        self.name_of_workspace = name_of_workspace
        self.number_of_channels = number_of_channels
        self.number_of_members = number_of_members

    def to_document(self):
        embedding = generate_embedding(self.name_of_workspace)
        return Document(
            page_content=self.name_of_workspace, 
            metadata={
            'id': self.team_id,
            'name_of_workspace': self.name_of_workspace,
            'number_of_channels': self.number_of_channels,
            'number_of_members': self.number_of_members
            }
        ), embedding

class Team_id:
    def __init__(self, channel_id, team_id, name_of_channel, number_of_members, number_of_messages):
        # id        
        self.channel_id = channel_id

        # metadata
        self.team_id = team_id
        self.name_of_channel = name_of_channel
        self.number_of_members = number_of_members
        self.number_of_messages = number_of_messages

    def to_document(self):
        embedding = generate_embedding(self.name_of_channel)
        return Document(
            page_content=self.name_of_channel, 
            metadata={
            'id': self.channel_id,
            'team_id': self.team_id,
            'name_of_channel': self.name_of_channel,
            'number_of_members': self.number_of_members,
            'number_of_messages': self.number_of_messages
            }
        ), embedding

class Channel_id:
    def __init__(self, message_id, person, datetime, message, reactions, replies):
        # id
        self.message_id = message_id
        
        # document
        self.message = message

        # metadata
        self.person = person
        self.datetime = datetime
        self.reactions = reactions
        self.replies = replies

    def to_document(self):
        embedding = generate_embedding(self.message)
        return Document(
            page_content=self.message, 
            metadata={
            'id': self.message_id,
            'person': self.person,
            'datetime': self.datetime,
            'reactions': self.reactions,
            'replies': self.replies
            }
        ), embedding

'''
For each class, will need to decide what the metadata will be
and what the document will be.
At the moment, team_ids and team_id don't seem to have metadata
'''