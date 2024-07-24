# app.py
import httpx, uvicorn, chromadb
from fastapi import FastAPI, HTTPException

from backend.modelsPydantic import (
    QueryResponse, QueryRequest, UpdateChannelInfo, UpdateChatHistory, 
    UpdateGuildInfo, UpdateMemberInfoChannel, UpdateMemberInfoGuild
)
from services.queryLangchain import fetchGptResponse, fetchLangchainResponse
from database.crudChroma import CRUD
from database.modelsChroma import (
    generate_embedding, ChatHistory, GuildInfo, ChannelInfo, MemberInfoGuild,
    MemberInfoChannel, ChannelList
)

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
async def resource_query(request: QueryRequest):

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

@app.post('/update_chat_history')
async def update_chat_history(request: UpdateChatHistory):
    all_messages = request.all_messages
    total_messages = sum([len(messages) for messages in all_messages.values()])
    chat_history = []
    for _, channel_messages in all_messages.items():
        for message in channel_messages:
            message_info = {
                "channel_id": message.channel_id,
                "channel_name": message.channel_name,
                "message_id": message.message_id,
                "author": message.author,
                "content": message.content,
                "timestamp": message.timestamp
            }
            # Pass the chat history to modelsChroma to get document and embedding
            try:
                chat_info = ChatHistory(message_info)
                document, embedding = await chat_info.to_document()
            except Exception as e:
                print(f"Error with updating chat history: {e}")
            
            chat_history.append({
                "collection_name": f"chat_history_{message_info["channel_id"]}",
                "document": document,
                "embedding": embedding
            })

    # Save chat history to Chromadb
    try:
        crud.save_to_db(chat_history)
    except Exception as e:
        print(f"Error with saving chat history: {e}")

    '''
    also need to implement saving general information
    '''
    print(f"Update complete, {total_messages} messages from {len(all_messages)} channels are loaded to the database.")
    return {"status": "Update complete"}

@app.post('/update_guild_info')
async def update_guild_info(request: UpdateGuildInfo):
    try:
        guild_info = GuildInfo(request.model_dump())
        document, embedding = await guild_info.to_document()
        data = {
            "collection_name": "guild_info",
            "document": document,
            "embedding": embedding
        }
        crud.save_to_db([data])

    except Exception as e:
        print(f"Error with updating guild info: {e}")

    print(f"Guild info updated for {request.guild_name}")
    return {"status": "Update complete"}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
