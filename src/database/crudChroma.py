# crudChroma.py
import chromadb

from utlis.config import DB_PATH
from database.modelsChroma import generate_embedding

class CRUD():
    def __init__(self):
        self.client = chromadb.PersistentClient(path = DB_PATH)
        
    def save_chat_history(self, chat_history):
        for chat in chat_history:
            collection_name, document, embedding= chat['channel_id'], chat['document'], chat['embedding']

            # change collection_name to type str since it was an int, but has to
            # be a str in order to be used as a collection name
            collection_name = str(collection_name)

            # note that collection_name is equivalent to channel_id
            collection = self.client.get_or_create_collection(collection_name)
            collection.add(
                # same for id, has to be a str
                ids=[str(document.metadata['id'])], 
                documents=[document.page_content],
                embeddings=[embedding], 
                metadatas=[document.metadata]
            )

            print(f"Here is the page content {document.page_content}")
        
        '''
        here might consider checking if the collection exists before using
        get_or_create_collection
        '''

    async def retrieve_relevant_history(self, channel_id, query_embedding, top_k=10):
        try:
            # Generate the embedding for the query
            collection_name = str(channel_id)  # Change from int to str
            print(f"Retrieving collection for channel ID: {collection_name}")

            # Get the collection
            collection = self.client.get_collection(collection_name)
            print(f"Collection retrieved: {collection}")

            # Query the collection
            results =  collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )

            for document in results["documents"]:
                print(f"Result: {document}")

            return results

        except Exception as e:
            print(f"Error with retrieving relevant history: {e}")
            return []

    