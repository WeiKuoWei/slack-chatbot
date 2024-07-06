import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains.question_answering import load_qa_chain
from crudChroma import CRUD

# Load environment variables
load_dotenv()

# Set up OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI embeddings model
embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")

# Initialize the ChromaDB client and retriever
chroma_client = Chroma(
    embedding_function=embedding_model,
    persist_directory="./local_chromadb",  # Adjust this to your actual DB_PATH if needed
    collection_name="C073U7920TZ"
)

# Initialize the language model
llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", max_tokens=500, openai_api_key=OPENAI_API_KEY)
chain = load_qa_chain(llm, chain_type="stuff", verbose=True)

# query = "What are the people in this research group trying to achieve?"
query = "What is going on in the channel recently?"
# query = "How are the team members feeling recently?"
# query = "Give me an update on the project progress recently."
# query = "How the team members in the project collaborate with each other?"

prompt = f'''
    {query} Write at least 100 words to answer the question. 
'''

matching_docs = chroma_client.similarity_search(query, k=10)
answer = chain.run(input_documents=matching_docs, question=prompt)
print(answer)

''' Here is an alternative way to run the query, which I have not seen apparent difference in the results.

# Initialize the RetrievalQA chain
chatbot_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=chroma_client.as_retriever(search_kwargs={"k": 10}), 
    verbose=True,
)

answer = chatbot_chain.run(query)
print(answer)
 '''