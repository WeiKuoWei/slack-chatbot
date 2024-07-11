import os
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains.question_answering import load_qa_chain

from utlis.config import OPENAI_API_KEY

# Initialize the OpenAI embeddings model
embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")

def fetchGptResponse(query, matching_docs):
    # Initialize the language model
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", max_tokens=500, openai_api_key=OPENAI_API_KEY)
    chain = load_qa_chain(llm, chain_type="stuff", verbose=True)
    prompt = f'''
        {query} Write at least 100 words to answer the question. 
    '''
    answer = chain.run(input_documents=matching_docs, question=prompt)
    return answer