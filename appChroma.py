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

load_dotenv()

# import functions
from messageExtractor import extract_messages, extract_reactions, get_workspace_info, get_channel_id, list_all_channels
from crudChroma import CRUD
from modelsChroma import Team_ids, Team_id, Channel_id

# for the team_ids collection

# for team_id collections

# for channel_id collections

# data file comparison
def compare_data(new_data, current_data):
    new_data = set(new_data)
    current_data = set(current_data)
    return new_data - current_data

# Main function
def main(
        token_name: str = "ZUCKER"
        ):

    # Initialize and connect to ChromaDB
    crud = CRUD()

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
    '''
    number of members
    are yet to be retrieved and saved to team_ids
    '''
    team_info = Team_ids(team_id=workspace_id, name_of_workspace=workspace_name, number_of_channels=len(channel_ids), number_of_members=0)
    crud.create_collection(f"{workspace_id}")
    document, embedding = team_info.to_document()
    crud.create_document(f"{workspace_id}", document, embedding)

    # load the list of channel_id into team_id
    '''
    number of members, number of messages 
    are yet to be retrieved and saved to team_id
    '''
    for channel_id, channel_name in channel_ids.items():
        channel_info = Team_id(channel_id=channel_id, team_id=workspace_id, name_of_channel=channel_name, number_of_members=0, number_of_messages=0)
        crud.create_collection(f"{channel_id}")
        document, embedding = channel_info.to_document()
        crud.create_document(f"{channel_id}", document, embedding)


    # load the list of messages into channel_id
    for channel_id, channel_name in channel_ids.items():
        # still need to be implemented
        continue


if __name__ == '__main__':
    fire.Fire(main)
