# app.py
import httpx, uvicorn, chromadb, time
from fastapi import FastAPI, HTTPException
from typing import Union

from backend.modelsPydantic import (
    QueryResponse, QueryRequest, UpdateChannelInfo, UpdateChatHistory, 
    UpdateGuildInfo, UpdateMemberInfo, UpdateChannelList
)
from services.queryLangchain import fetchGptResponse, fetchLangchainResponse, fetchGptResponseTwo
from services.nlpTools import TextProcessor
from database.crudChroma import CRUD
from database.modelsChroma import (
    generate_embedding, ChatHistory, GuildInfo, ChannelInfo, MemberInfoChannel, ChannelList
)

from utlis.config import DB_PATH

app = FastAPI()
crud = CRUD()

CHANNEL_SUMMARIZER = '''
    You are a channel messages summarizer. You will be the most relevant
    messages to the user query. Answer the user as detailed as possible.
'''

COURSE_INSTRUCTOR = '''
    You are a course instructor. You will be given the most relevant 
    course materials to the user query. Answer the user as detail as possible.
'''


@app.post('/channel_query') #, response_model=QueryResponse
async def channel_query(request: QueryRequest):
    try:
        query_embedding = await generate_embedding(request.query)
        collection_name = f"chat_history_{request.channel_id}"
        relevant_docs = await crud.get_data_by_similarity(collection_name, query_embedding, top_k=5)
        channel_info = await crud.get_data_by_id(f"channel_info_{request.guild_id}", [request.channel_id])
        
        content = relevant_docs.get('documents')[0]
        data = channel_info.get('metadatas')[0]
        print(f"Relevant messages: {content}")
        print(f"Channel info: {data}")

        # combine the relevant messages and channel info
        combined_data = {
            'relevant_messages': content,
            'channel_info': channel_info
        }

        answer = await fetchGptResponse(request.query, CHANNEL_SUMMARIZER , combined_data)
        print(f"Answer: {answer}")
        return {'answer': answer}  
    
    except Exception as e:
        print(f"Error with channel related question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/resource_query') #, response_model=QueryResponse
async def resource_query(request: QueryRequest):
    try:
        query_embedding = await generate_embedding(request.query)
        collection_name = "course_materials"
        relevant_docs = await crud.get_data_by_similarity(collection_name, query_embedding, top_k=5)
        
        content = relevant_docs.get('documents')[0]
        print(f"Relevant messages: {content}")

        answer = await fetchGptResponse(request.query, COURSE_INSTRUCTOR , relevant_docs)
        print(f"Answer: {answer}")
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
                "author_id": message.author_id,
                "content": message.content,
                "timestamp": message.timestamp,
                "profanity_score": message.profanity_score
            }
            # Pass the chat history to modelsChroma to get document and embedding
            try:
                chat_info = ChatHistory(message_info)
                document, embedding = await chat_info.to_document()
            except Exception as e:
                print(f"Error with updating chat history: {e}")
            
            chat_history.append({
                "collection_name": f"chat_history_{message_info.get('channel_id')}",
                "document": document,
                "embedding": embedding
            })

    # Save chat history to Chromadb
    try:
        await crud.save_to_db(chat_history)
    except Exception as e:
        print(f"Error with saving chat history: {e}")

    print(f"Update complete, {total_messages} messages from {len(all_messages)} channels are loaded to the database.")
    return {"status": "Update complete"}

@app.post('/update_info')
async def update_info(request: Union[UpdateGuildInfo, UpdateChannelInfo, UpdateMemberInfo, UpdateChannelList]):
    try:
        if isinstance(request, UpdateGuildInfo):
            collection_name = "guild_info"
            info = GuildInfo(request.model_dump())

        elif isinstance(request, UpdateChannelInfo):
            collection_name = f"channel_info_{request.guild_id}"
            info = ChannelInfo(request.model_dump())
        
        elif isinstance(request, UpdateMemberInfo):
            collection_name = f"member_info_{request.channel_id}"
            info = MemberInfoChannel(request.model_dump())
        
        elif isinstance(request, UpdateChannelList):
            collection_name = f"channel_list_{request.guild_id}"
            info = ChannelList(request.model_dump())
        
        document, embedding = await info.to_document()
        data = {
            "collection_name": collection_name,
            "document": document,
            "embedding": embedding
        }
        await crud.save_to_db([data])

    except Exception as e:
        print(f"Error with updating guild info: {e}")

    print(f"Info updated for {collection_name}")
    return {"status": "Update complete"}

@app.post('/load_course_materials')
async def load_course_materials():
    file_path = "./data/pdf_files"
    collection_name = "course_materials"
    try:
        data = await crud.save_pdfs(file_path, collection_name)

        # save the data to the database in chunks of ten documents
        chunk_size = 10
        for i in range(0, len(data), chunk_size):
            await crud.save_to_db(data[i:i+chunk_size])

        return {"message": "PDFs loaded successfully."}
    
    except Exception as e:
        print(f"app.py: Error with loading PDFs: {e}")
        return {"message": "Failed to load PDFs."}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
