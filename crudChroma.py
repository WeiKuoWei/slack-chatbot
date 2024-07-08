import chromadb, os
from langchain.schema import Document
from chromadb.config import Settings
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()

DB_PATH = os.getenv("DB_PATH")
embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")

class CRUD():
    def __init__(self):
        self.client = chromadb.PersistentClient(path = DB_PATH)
        
        '''
        self.client = Chroma(
            embedding_function=embedding_model,
            persist_directory="./local_chromadb",  # Adjust this to your actual DB_PATH if needed
            collection_name="C073U7920TZ"
        )
        '''
    def get_client(self):
        return self.client

    def create_collection(self, collection_name):
        collection = self.client.get_or_create_collection(collection_name)
        return collection

    def create_document(self, collection_name, document, embedding):
        collection = self.client.get_collection(collection_name)
        collection.add(
            ids=[document.metadata['id']], 
            documents=[document.page_content],
            embeddings=[embedding], 
            metadatas=[document.metadata]
        )
        '''
            seems to be missing the document itself
            would need to differentiate between the metadata and the document
        '''
    def retrieve_collection(self, collection_name):  
        return self.client.get_collection(collection_name)

    def query_collection(self, collection_name, embedded_query, n_results=1):
        collection = self.client.get_collection(collection_name)
        return collection.query(
                    query_embeddings = embedded_query,
                    n_results = n_results
                )

    # def update(self, collection_name, query, new_values):
    #     # Update logic for ChromaDB
    #     pass

    # def delete_document(self, collection_name, query):
    #     collection = self.client.get_collection(collection_name)
    #     collection.delete(query)

    # def delete_collection(self, collection_name):
    #     self.client.delete_collection(collection_name)
