import os, asyncio
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from google import genai
from google.genai.types import GenerateContentConfig
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.utlis.config import OPENAI_API_KEY, DB_PATH, DISTANCE_THRESHOLD, GEMINI_API_KEY
from src.utlis.prompts import PROMPTS

# llm = ChatOpenAI(
#     temperature=0,
#     model_name="gpt-3.5-turbo",
#     max_tokens=500,
#     openai_api_key=OPENAI_API_KEY
# )

# client = OpenAI(api_key=OPENAI_API_KEY)

gem_client = genai.Client(api_key=GEMINI_API_KEY)

# Create the request configuration
config = GenerateContentConfig(
    system_instruction=PROMPTS['reroute_expert']
)

# Define the user prompt
# prompt = "Can you explain what a Python class is?"
query = "Query: Are there any guides for lab 2? Chosen Route: progress_report"
def generateGeminiRespone(query: str, config):
    response = gem_client.models.generate_content(
        model="gemini-1.5-flash",
        contents=query,
        config=config
    )
    return response.text
    # return answer[8:].lower()
n = generateGeminiRespone(query, config)
print(n.find('No'))
print(n.find('no'))
print(n.find('yes'))
revised_idx = n.find('Revised Query: ')
print(n[revised_idx+15:])
# print(n[8:].lower())
'''
Here, three different versions of the fetchGptResponse function are defined.
From the average of testing the time taken for each version, here are the average time:
fetchLangchainResponse: 2.840806246	
fetchGptResponseTwo: 4.176655531	
fetchGptResponse: 3.762374473
'''


# async def fetchGptResponse(query, role, data=[]):
#     response = await asyncio.to_thread(
#         llm.invoke,
#         [
#             ("system", f"{role} Here are the relevant information {str(data)}."),
#             ("user", query)
#         ]
#     )
#     return response.content


# async def fetchLangchainResponse(query, collection_name, top_k=10):

#     embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")
#     # embedding_model = SentenceTransformerEmbeddings(model="all-MiniLM-L6-v2")

#     # Initialize the ChromaDB client and retriever
#     client = Chroma(
#         embedding_function=embedding_model,
#         persist_directory=DB_PATH, 
#         collection_name=str(collection_name)
#     )

#     try:
#         # Initialize the RetrievalQA chain
#         chatbot_chain = RetrievalQA.from_chain_type(
#             llm=llm,
#             chain_type="stuff",
#             retriever=client.as_retriever(
#                 search_type="similarity_score_threshold", 
#                 search_kwargs={"k": top_k, "score_threshold": DISTANCE_THRESHOLD}
#             ),
#             verbose=True, 
#             return_source_documents=True,
#         )

#         # Define the prompt template
#         template = f"""
#         Respond as clearly as possible with more than 100 words {query}?
#         """

#         prompt = PromptTemplate(
#             input_variables=["query"],
#             template=template,
#         )

#         # Run the query through the chatbot chain
#         response = chatbot_chain.invoke(prompt.format(query=query))

#         # Extract and print source documents
#         source_documents = response.get('source_documents', [])
#         sources = [doc.metadata['source'] for doc in source_documents]
#         sources = list(set(sources))
#         response["sources"] = sources

#         return response

#     except Exception as e:
#         print(f"Error with fetching Langchain response: {e}")
#         return "I'm sorry, I couldn't find an answer to that question."


# async def fetchGptResponseTwo(query, role, data=[]):
#     messages = [
#         {"role": "system", "content": role},
#         {"role": "user", "content": f"Here are the relevant information: {str(data)}"},
#         {"role": "user", "content": query},
#     ]

#     try:
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=messages,
#             temperature=0,
#             max_tokens=500,
#         )

#         print(f"Response from OpenAI: {response}")
#         assistant_reply = response.choices[0].message.content
#         return assistant_reply
    
#     except Exception as e:
#         print(f"Error with fetching GPT response: {e}")
#         return "I'm sorry, I couldn't find an answer to that question."
