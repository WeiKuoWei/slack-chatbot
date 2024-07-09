# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from chromadb import Client

app = FastAPI()
chromadb_client = Client()

@app.post('/query')
async def query_chat_data(request: QueryRequest):
    # Fetch relevant chat data from Chromadb
    chat_data = chromadb_client.query(request.query, request.channel)
    
    # Send chat data to ChatGPT API
    async with httpx.AsyncClient() as client:
        response = await client.post('https://api.openai.com/v1/engines/davinci-codex/completions', json={
            'prompt': chat_data,
            'max_tokens': 150,
            'temperature': 0.7
        }, headers={'Authorization': f'Bearer YOUR_OPENAI_API_KEY'})
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error with ChatGPT API")
    
    answer = response.json()['choices'][0]['text']
    return {'answer': answer}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
