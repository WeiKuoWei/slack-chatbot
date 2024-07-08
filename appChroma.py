import json, fire, os, chromadb, discord

from slack_sdk import WebClient
from dotenv import load_dotenv

# import functions
from getMessageDiscord import getMessage
from crudChroma import CRUD
from modelsChroma import Channel_info

load_dotenv()
crud = CRUD()
'''
Not sure if this might be become a single breakpoint for the entire app.
Still considering initializing crud in each function
'''

# for channel_id collections
def save_to_channel_id(channel_id, data):
    for message in data:
        message_info = Channel_info(message)
        document, embedding = message_info.to_document()
        crud.create_document(f"{channel_id}", document, embedding)

# data file comparison
def compare_data(new_data, current_data):
    new_data = set(new_data)
    current_data = set(current_data)
    return new_data - current_data

# Main function
def main(
        channel_id,
        workspace_id,
        token_name, 
        endpoint: str = "DISCORD"        
        ):

    # get workspace info
    USER_TOKEN = os.getenv(f"{token_name}_USER_TOKEN")
    if endpoint == "DISCORD":
        intents = discord.Intents.default()
        intents.message_content = True

        # Instantiate the getMessage client with intents
        client = getMessage(intents=intents)
        client.run(USER_TOKEN)
    
    else:
        slack_client = WebClient(token=USER_TOKEN)


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
