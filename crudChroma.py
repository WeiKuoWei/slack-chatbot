import chromadb, os
from langchain.schema import Document
from dotenv import load_dotenv


DB_PATH = os.getenv("DB_PATH")

class CRUD():
    def __init__(self):
        self.client = chromadb.PersistentClient(path = DB_PATH)

    def create_collection(self, collection_name):
        collection = self.client.get_or_create_collection(collection_name)
        return collection

    def create_document(self, collection_name, document, embedding):
        collection = self.client.get_collection(collection_name)
        collection.add(
            ids=[document.metadata['id']],  # Ensure IDs are passed as a list
            embeddings=[embedding], 
            # here will need to update the embeddings in the future
            metadatas=[document.metadata]
        )

    def read(self, collection_name, query):
        collection = self.client.get_collection(collection_name)
        return collection.search(query)

    def update(self, collection_name, query, new_values):
        # Update logic for ChromaDB
        pass

    def delete_document(self, collection_name, query):
        collection = self.client.get_collection(collection_name)
        collection.delete(query)

    def delete_collection(self, collection_name):
        self.client.delete_collection(collection_name)


'''
This is an alternative implementation of the CRUD class that take collection_name as an argument in the constructor. 
An instance of this class can be created for each collection. Save for later if the current implementation is not working.

class CRUD():
    def __init__(self, collection_name):
        self.client = chromadb.PersistentClient(path = DB_PATH)
        self.collection_name = collection_name # return self.client

    def create_collection(self, documents):
        collection = self.client.create_or_get_collection(self.collection_name)
        return collection

    def create_document(self, document):
        collection = self.client.get_collection(self.collection_name)
        collection.add_document(document)

    def read(self, query):
        collection = self.client.get_collection(self.collection_name) return
        collection.search(query)

    def update(self, query, new_values):
        # Update logic for ChromaDB pass

    def delete_document(self, query):
        collection = self.client.get_collection(self.collection_name)
        collection.delete(query)

    def delete_collection(self):
        self.client.delete_collection(self.collection_name)
'''
