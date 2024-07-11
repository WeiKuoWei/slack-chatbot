import os, asyncio
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains.question_answering import load_qa_chain

from utlis.config import OPENAI_API_KEY

async def fetchGptResponse(query, query_kind, matching_docs=[]):
    llm = ChatOpenAI(
        temperature=0,
        model_name="gpt-3.5-turbo",
        max_tokens=500,
        openai_api_key=OPENAI_API_KEY
    )

    # if it's a general question
    if query_kind is False:  
        response = await asyncio.to_thread(
            llm.invoke,
            [
                ("system", "You are a helpful assistant."),
                ("user", query)
            ]
        )
        print(response)
        return response.content

    if len(matching_docs) == 0:
        return "No matching documents found. Please try again."
    
    # is not empty, proceed with the QA chain
    chain = load_qa_chain(llm, chain_type="stuff", verbose=True)
    prompt = f'''
        {query} Write at least 100 words to answer the question. 
    '''
    
    response = await asyncio.to_thread(chain.run, input_documents=matching_docs, question=prompt)
    
    return response