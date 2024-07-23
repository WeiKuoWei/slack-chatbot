# app.py
import httpx, uvicorn, chromadb
from fastapi import FastAPI, HTTPException

from backend.modelsPydantic import (
    QueryRequest, UpdateRequest, QueryResponse
)

from services.gptAssistant import fetchAssistanceResponse
from services.queryLangchain import fetchGptResponse, fetchLangchainResponse
from database.crudChroma import CRUD
from database.modelsChroma import ChatHistory, generate_embedding
from utlis.config import DB_PATH

app = FastAPI()
crud = CRUD()

@app.post('/channel_query') #, response_model=QueryResponse
async def channel_query(request: QueryRequest):
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
        print(f"Error with channel related question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/resource_query') #, response_model=QueryResponse
async def channel_query(request: QueryRequest):

    try:
        # retrieve chat data from Chromadb here
        try:
            collection_name = "course_materials"
            answer = await fetchLangchainResponse(request.query, collection_name)

        except Exception as e:
            print(f"Error with Langchain response: {e}")
        return {'answer': answer}  
    
    except Exception as e:
        print(f"Error with course material related question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

    '''
    also need to implement saving general information
    '''
    print(f"Update complete, {len(chat_history)} channels with {len(messages)} messages loaded.")
    return {"status": "Update complete"}

async def get_channel_history(channel_id):
    # Implement this function to interact with Discord API and fetch channel history
    # This can be done using discord.py or directly via Discord API
    pass

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
