# app.py
import httpx, uvicorn, chromadb
from fastapi import FastAPI, HTTPException

from backend.modelsPydantic import QueryRequest, UpdateRequest
from services.queryLangchain import fetchGptResponse
from database.crudChroma import CRUD
from database.modelsChroma import ChatHistory
from utlis.config import DB_PATH

app = FastAPI()
crud = CRUD()
chromadb_client = chromadb.PersistentClient(path=DB_PATH)

@app.post('/query')
async def query_chat_data(request: QueryRequest):
    # Fetch relevant chat data from Chromadb
    matching_docs = chromadb_client.query(request.query, request.channel)
    
    # Send chat data to ChatGPT API
    try:
        answer = await fetchGptResponse(request.query, matching_docs)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Error with ChatGPT API")
    
    return {'answer': answer}

@app.post('/update')
async def update_chat_history(request: UpdateRequest):
    guild_id = request.guild_id
    channels = request.channels
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

async def get_channel_history(channel_id):
    # Implement this function to interact with Discord API and fetch channel history
    # This can be done using discord.py or directly via Discord API
    pass

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
