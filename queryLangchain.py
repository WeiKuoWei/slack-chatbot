import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from crudChroma import CRUD

# Load environment variables
load_dotenv()

# Set up OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI embeddings model
# embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=OPENAI_API_KEY)
embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")

# Initialize the ChromaDB client and retriever
chroma_client = Chroma(
    embedding_function=embedding_model,
    persist_directory="./local_chromadb",  # Adjust this to your actual DB_PATH if needed
    collection_name="C073U7920TZ"
)

# crud = CRUD()
# chroma_client = crud.get_client()

# Initialize the language model
llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", max_tokens=500, openai_api_key=OPENAI_API_KEY)

# Initialize the RetrievalQA chain
chatbot_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=chroma_client.as_retriever(search_kwargs={"k": 2})
)

# Define the prompt template
template = """
respond as clearly as possible {query}?
"""

prompt = PromptTemplate(
    input_variables=["query"],
    template=template,
)

# Run the query through the chatbot chain
response = chatbot_chain.invoke(prompt.format(query="Summarize what is going on in this channel?"))
print(response)
