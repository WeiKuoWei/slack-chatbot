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
        embedding = generate_embedding(self.team_id)
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
        embedding = generate_embedding(self.channel_id)
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
            '''
            reactions is not added since it is a list; metadata has to be either
            type str, int, float, or bool to be added to the document
            '''
            'replies': self.replies
            }
        ), embedding
    

'''
For each class, will need to decide what the metadata will be and what the
document will be. At the moment, team_ids and team_id don't seem to have
metadata

Moreover, team_ids and team_id takes the parameters directly, while channel_id
takes a data dictionary and unpack the necessary parameters. This is temporary
as the json file for teams_ids and team_id will need to be updated to include
other necessary parameters for the metadata. This should be done as soon as the
information retrieval functions are implemented.
'''