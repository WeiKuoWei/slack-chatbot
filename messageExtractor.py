import json
import re
import os

from datetime import datetime as dt
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()
slack_token = os.getenv("SLACK_API_TOKEN")

# Set your Slack API token
# slack_token = env_variables["SLACK_API_TOKEN"]
client = WebClient(token=slack_token)

def extract_reactions(reactions):
    extracted_reactions = []
    for reaction in reactions:
        extracted_reactions.append({
            "emoji": reaction['name'],
            "count": reaction['count']
        })
    return extracted_reactions

def extract_messages(channel_id):
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
        user_name = user_info['user']['real_name']

        # Replace user IDs with real names in the message
        tagged_users = re.findall(r'<@(.*?)>', message['text'])
        for user_id in tagged_users:
            user_info = client.users_info(user=user_id)
            user_name = user_info['user']['real_name']
            message['text'] = message['text'].replace(f'<@{user_id}>', user_name)

        timestamp = float(message['ts'])
        dt_object = dt.fromtimestamp(timestamp)
        formatted_datetime = dt_object.strftime('%Y-%m-%d %I:%M %p')

        extracted_messages.append({
            "id": i,
            "person": user_name,
            "datetime": formatted_datetime,
            "message": message['text'],
            "reactions": extract_reactions(message.get('reactions', [])),
            "replies": message.get('reply_count', 0)
        })
    return extracted_messages

def save_to_json(data, file_path):
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def main():
    # Set the ID of the public Slack channel you want to read 
    # NOTES: will need to automate this process, find all channel IDs, and save them into a json file
    channel_id = 'C079049992M'

    # Extract the messages from the channel
    messages = extract_messages(channel_id)

    # Save the messages to a JSON file
    save_to_json(messages, 'slack_messages.json')

if __name__ == '__main__':
    main()