
import httpx
import uvicorn
import chromadb
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from .extract_to_json import extract_metadata_to_json
from collections import defaultdict

from backend.modelsPydantic import (
    QueryRequest, UpdateRequest, QueryResponse
)
from services.gptAssistant import fetchAssistanceResponse
from services.queryLangchain import fetchGptResponse, fetchLangchainResponse
from database.crudChroma import CRUD
from database.modelsChroma import ChatHistory, generate_embedding
from utlis.config import DB_PATH 

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
crud = CRUD()
DATABASE_PATH = os.getenv('DB_PATH') + '/chroma.sqlite3'

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

metadata_path = extract_metadata_to_json()
def load_metadata():
    try:
        with open(metadata_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading metadata JSON: {e}")
        return []

metadata = load_metadata()

namedir = defaultdict(str)
for entry in metadata:
    if not namedir[str(entry['topic'])]:
        namedir[str(entry['topic'])] = str(entry['channel_name'])


print(namedir)
class TimeQueryRequest(BaseModel):
    channel_id: str
    start_time: datetime
    end_time: datetime

async def fetch_guilds_and_channels():
    try:
        collections = crud.client.list_collections()
        
        return collections
    except Exception as e:
        logger.error(f"Error fetching collections: {e}")
        return []

@app.get('/guilds_and_channels')
async def get_guilds_and_channels():
    try:
        logger.info(f"Fetching guilds and channels from database: {DATABASE_PATH}")
        collections = await fetch_guilds_and_channels()
        guilds_channels = {'main': {'guild_name': 'main', 'channels': []}}
        for collection in collections:
            channel_id = crud.client.get_collection(collection.name).get_model()['id']
            channel_name = namedir[str(channel_id)]
            guilds_channels['main']['channels'].append({'channel_id': channel_id, 'channel_name': channel_name})
        # print(guilds_channels)
        return guilds_channels
    except Exception as e:
        logger.error(f"Error fetching guilds and channels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/general') # , response_model=QueryResponse
async def general_question(request: QueryRequest):

    try:
        # retrieve chat data from Chromadb here
        try:
            query_embedding = await generate_embedding(request.query)
            relevant_docs = await crud.retrieve_relevant_history(request.channel_id, query_embedding)
            
            for key, value in relevant_docs.items():
                print(f"Key: {key}, Value: {value}")

            formatted_messages = []
            unique_authors = set()

            for metadata, document in zip(relevant_docs['metadatas'][0], relevant_docs['documents'][0]):
                author = metadata['author']
                timestamp = metadata['timestamp']
                content = document
                unique_authors.add(author)
                
                formatted_messages.append(f"Author: {author}\nTimestamp: {timestamp}\nMessage: {content}\n")

            channel_name = relevant_docs['metadatas'][0][0]['channel_name']

            data = {
                "channel_name": channel_name,
                "authors": unique_authors,
                "number_of_unique_authors": len(unique_authors),
                "messages": formatted_messages
            }

            answer = await fetchGptResponse(request.query, data)
            print(f"Answer: {answer}")

        except Exception as e:
            print(f"Error with GPT response: {e}")

        return {'answer': answer}  
    
    except Exception as e:
        print(f"Error with general question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/super') # , response_model=QueryResponse
async def super_question(request: QueryRequest):
    try:
        logger.info(f"Received payload: {request.dict()}")  # Log received payload
        # retrieve chat data from Chromadb here
        try:
            query_embedding = await generate_embedding(request.query)
            relevant_docs = await crud.retrieve_relevant_history(request.channel_id, query_embedding)
            
            for key, value in relevant_docs.items():
                logger.info(f"Key: {key}, Value: {value}")

            formatted_messages = []
            unique_authors = set()

            for metadata, document in zip(relevant_docs['metadatas'][0], relevant_docs['documents'][0]):
                author = metadata['author']
                timestamp = metadata['timestamp']
                content = document
                unique_authors.add(author)
                
                formatted_messages.append(f"Author: {author}\nTimestamp: {timestamp}\nMessage: {content}\n")

            channel_name = relevant_docs['metadatas'][0][0]['channel_name']

            data = {
                "channel_name": channel_name,
                "authors": unique_authors,
                "number_of_unique_authors": len(unique_authors),
                "messages": formatted_messages
            }

            answer = await fetchGptResponse(request.query, data)
            logger.info(f"Answer: {answer}")

        except Exception as e:
            logger.error(f"Error with GPT response: {e}")

        return {'answer': answer}  
    
    except Exception as e:
        logger.error(f"Error with super question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/query_channel', response_model=QueryResponse)
async def query_chat_data(request: QueryRequest):
    print("query_channel")
    try:
        answer = fetchAssistanceResponse(
            request.guild_id,
            request.channel_id, 
            request.query,            
        )

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Error with ChatGPT API")
    
    return {'answer': answer}

@app.post('/update')
async def update_chat_history(request: UpdateRequest):
    '''
    at the moment, guild_id and channel_id are passed but not used
    '''
    messages = request.messages

    chat_history = []
    for message in messages:
        message_info = {
            "channel_id": message.channel_id,
            "channel_name": message.channel_name,
            "message_id": message.message_id,
            "author": message.author,
            "content": message.content,
            "timestamp": message.timestamp
        }
        # Pass the chat history to modelsChroma to get document and embedding
        chat_info = ChatHistory(message_info)
        document, embedding = await chat_info.to_document()
        
        chat_history.append({
            "channel_id": message_info["channel_id"],
            "document": document,
            "embedding": embedding
        })

    # Save chat history to Chromadb
    crud.save_chat_history(chat_history)
    print(f"Update complete, {len(chat_history)} channels with {len(messages)} messages loaded.")
    return {"status": "Update complete"}

@app.post('/query_time_period')
async def query_time_period(request: TimeQueryRequest):
    try:
        logger.info(f"Fetching messages from JSON for channel {request.channel_id} from {request.start_time} to {request.end_time}")
        messages = fetch_messages_within_time_period(request.channel_id, request.start_time, request.end_time)
        logger.info(f"Fetched messages: {messages}")
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def fetch_messages_within_time_period(channel_id, start_time, end_time):
    print(channel_id)
 
    start_time = start_time.replace(tzinfo=timezone.utc)
    end_time = end_time.replace(tzinfo=timezone.utc)
    messages = []
    for entry in metadata:
        if str(entry['topic']) == str(channel_id):
            
            timestamp = datetime.fromisoformat(entry.get('timestamp'))
            if start_time <= timestamp <= end_time:
                messages.append(entry)

    return messages

if __name__ == '__main__':
    
    uvicorn.run(app, host='0.0.0.0', port=8000)
