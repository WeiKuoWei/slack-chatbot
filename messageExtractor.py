import json
import re
import os
import fire
from datetime import datetime as dt
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import argparse

# Load environment variables from .env file
load_dotenv()

def extract_reactions(reactions):
    extracted_reactions = []
    for reaction in reactions:
        extracted_reactions.append({
            "emoji": reaction['name'],
            "count": reaction['count']
        })
    return extracted_reactions

def get_workspace_info(client):
    try:
        response = client.auth_test()
        team_name = response['team']
        team_id = response['team_id']
        return team_name, team_id
    
    except SlackApiError as e:
        print(f"Error fetching workspace name: {e.response['error']}")
        return None

def extract_messages(client, channel_id):
    try:
        response = client.conversations_history(channel=channel_id)
        messages = response['messages']
        while response['has_more']:
            response = client.conversations_history(
                channel=channel_id,
                cursor=response['response_metadata']['next_cursor']
            )
            messages.extend(response['messages'])
    except SlackApiError as e:
        print(f"Error retrieving messages: {e.response['error']}")
        return []

    extracted_messages = []
    for i, message in enumerate(messages, start=1):
        user_info = client.users_info(user=message['user'])
        user_name = user_info['user'].get('real_name', user_info['user'].get('name', 'Unknown'))

        # Replace user IDs with real names in the message
        tagged_users = re.findall(r'<@(.*?)>', message['text'])
        for user_id in tagged_users:
            user_info = client.users_info(user=user_id)
            user_name = user_info['user'].get('real_name', user_info['user'].get('name', 'Unknown'))
            message['text'] = message['text'].replace(f'<@{user_id}>', user_name)

        # Extract and use the unique timestamp as the key
        unique_timestamp = message['ts']
        timestamp = float(unique_timestamp)
        dt_object = dt.fromtimestamp(timestamp)
        formatted_datetime = dt_object.strftime('%Y-%m-%d %I:%M %p')

        extracted_messages.append({
            "id": unique_timestamp,
            "person": user_name,
            "datetime": formatted_datetime,
            "message": message['text'],
            "reactions": extract_reactions(message.get('reactions', [])),
            "replies": message.get('reply_count', 0)
        })
    return extracted_messages

def save_to_json(data, name, path):
    file_path = os.path.join(path, name)
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def get_channel_id(client, channel_name):
    cursor = None
    try:
        while True:
            response = client.conversations_list(limit=1000, cursor=cursor)
            channels = response['channels']
            for channel in channels:
                if channel['name'] == channel_name:
                    print(f"Found channel {channel_name} with id {channel['id']}")
                    return channel['id']
            cursor = response.get('response_metadata', {}).get('next_cursor')
            if not cursor:
                break
    except SlackApiError as e:
        print(f"Error: {e.response['error']}")

def list_all_channels(client):
    cursor = None
    channels = []
    try:
        while True:
            response = client.conversations_list(limit=1000, cursor=cursor)
            channels.extend(response['channels'])
            cursor = response.get('response_metadata', {}).get('next_cursor')
            if not cursor:
                break
    except SlackApiError as e:
        print(f"Error retrieving channels: {e.response['error']}")
        return []

    channel_names = [channel['name'] for channel in channels]
    return channel_names

def main(
        token_name: str = "ZUCKER"
):
    # Set your Slack API token
    SLACK_USER_TOKEN = os.getenv(f"{token_name}_USER_TOKEN")
    client = WebClient(token=SLACK_USER_TOKEN)
    
    workspace_name, workspace_id = get_workspace_info(client)
    channel_names = list_all_channels(client)
    channel_ids = {}
    print("List of all channels:")
    for name in channel_names:
        print(name)
        id = get_channel_id(client, name)
        channel_ids[id] = name

    # File path
    # Append the workspace name and workspace id pair to a json file
    path = os.path.join("data", "workspace_list.json")

    # import the dictionary from the json file
    with open(path, 'r') as f:
        data = json.load(f)
    data[workspace_id] = workspace_name

    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

    # Create directory for the workspace
    path = os.path.join("data", workspace_id)
    os.makedirs(path, exist_ok=True)

    # Extract the messages from the channel
    for channel_id, _ in channel_ids.items():
        messages = extract_messages(client, channel_id)

        # Save the messages to a JSON file
        save_to_json(messages, f'{channel_id}.json', path)

    # save channel names and ids to a json file
    save_to_json(channel_ids, f'channel_list.json', path)

if __name__ == '__main__':
    fire.Fire(main)
