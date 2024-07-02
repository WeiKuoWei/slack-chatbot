import json, fire, os, chromadb

from slack_sdk import WebClient
# from langchain.embeddings.openai import OpenAIEmbeddings
# from langchain.vectorstores import Chroma
# from langchain.document_loaders import JSONLoader
# from langchain.text_splitter import CharacterTextSplitter
# from langchain.vectorstores import Chroma
# from langchain.document_loaders import JSONLoader
# from langchain.schema import Document
from dotenv import load_dotenv

# import functions
from messageExtractor import extract_messages, extract_reactions, get_workspace_info, get_channel_id, list_all_channels
from crudChroma import CRUD
from modelsChroma import Team_ids, Team_id, Channel_id

load_dotenv()
crud = CRUD()
'''
Not sure if this might be become a single breakpoint for the entire app.
Still considering initializing crud in each function
'''

# for the team_ids collection
def save_to_team_ids(workspace_id, workspace_name, channel_ids, n_members):
    '''
    number of members
    are yet to be retrieved and saved to team_ids
    '''
    team_info = Team_ids(team_id=workspace_id, 
                         name_of_workspace=workspace_name, 
                         number_of_channels=len(channel_ids), 
                         number_of_members=n_members
                        )
    crud.create_collection(f"{workspace_id}")
    document, embedding = team_info.to_document()
    crud.create_document(f"{workspace_id}", document, embedding)

# for team_id collections
def save_to_team_id(channel_id, channel_name, workspace_id, n_members, n_messages):
    '''
    number of members, number of messages 
    are yet to be retrieved and saved to team_id
    '''
    channel_info = Team_id(
        channel_id=channel_id, 
        team_id=workspace_id, 
        name_of_channel=channel_name, 
        number_of_members=0, 
        number_of_messages=0
        )
    
    crud.create_collection(f"{workspace_id}")
    document, embedding = channel_info.to_document()
    crud.create_document(f"{workspace_id}", document, embedding)

# for channel_id collections
def save_to_channel_id(channel_id, data):
    for message in data:
        message_info = Channel_id(message)
        document, embedding = message_info.to_document()
        crud.create_document(f"{channel_id}", document, embedding)

# data file comparison
def compare_data(new_data, current_data):
    new_data = set(new_data)
    current_data = set(current_data)
    return new_data - current_data

# Main function
def main(
        token_name: str = "ZUCKER" 
        ):

    # get workspace info
    SLACK_USER_TOKEN = os.getenv(f"{token_name}_USER_TOKEN")
    slack_client = WebClient(token=SLACK_USER_TOKEN)
    workspace_name, workspace_id = get_workspace_info(slack_client)
    
    # get channel info for this workspace
    channel_names = list_all_channels(slack_client)
    channel_ids = {}
    for name in channel_names:
        id = get_channel_id(slack_client, name)
        channel_ids[id] = name

    # load the workspace data in ChromaDB
    save_to_team_ids(workspace_id, workspace_name, channel_ids, 0)

    # for team_id collections and channel_id collections
    for channel_id, channel_name in channel_ids.items():
        # load the list of channel_id into team_id
        save_to_team_id(channel_id, channel_name, workspace_id, 0, 0)

        # load the channel_id data into channel_id collection
        crud.create_collection(f"{channel_id}")
        path = os.path.join(f"data/{workspace_id}", f"{channel_id}.json")
        with open(path, 'r') as json_file:
            data = json.load(json_file)
            save_to_channel_id(channel_id, data)
            '''
            the old/ new data comparison logic will be implemented here
            to insert only new data into the channel_id collection
            '''


if __name__ == '__main__':
    fire.Fire(main)
