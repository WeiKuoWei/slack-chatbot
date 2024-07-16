# app.py
import httpx, uvicorn, chromadb
from fastapi import FastAPI, HTTPException

from backend.modelsPydantic import (
    QueryRequest, UpdateRequest, QueryResponse
)

from services.gptAssistant import fetchAssistanceResponse
from services.queryLangchain import fetchGptResponse
from database.crudChroma import CRUD
from database.modelsChroma import ChatHistory, generate_embedding
from utlis.config import DB_PATH

app = FastAPI()
crud = CRUD()
chromadb_client = chromadb.PersistentClient(path=DB_PATH)


@app.post('/general', response_model=QueryResponse)
async def general_question(request: QueryRequest):
    try:
        # retrieve chat data from Chromadb here
        query_embedding = await generate_embedding(request.query)
        relevant_docs = await crud.retrieve_relevant_history(request.channel_id, query_embedding)
        print("answer")
        answer = await fetchGptResponse(request.query, False, relevant_docs)
        return {'answer': answer}  
    
    except Exception as e:
        print(f"Error with general question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/query_channel', response_model=QueryResponse)
async def query_chat_data(request: QueryRequest):
    print("query_channel")
    # Send chat data to ChatGPT API
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

async def get_channel_history(channel_id):
    # Implement this function to interact with Discord API and fetch channel history
    # This can be done using discord.py or directly via Discord API
    pass

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
