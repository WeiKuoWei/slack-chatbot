# crudChroma.py
import chromadb

from utlis.config import DB_PATH

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
        '''
        here might consider checking if the collection exists before using
        get_or_create_collection
        '''