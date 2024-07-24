# crudChroma.py
import chromadb, uuid, os

from utlis.config import DB_PATH
from utlis.getFileDir import findFileBFS
from database.modelsChroma import generate_embedding
from services.getPdfs import read_hyperlinks, match_filenames_to_urls
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader
from langchain_openai import OpenAIEmbeddings

# temp
from langchain.chains.question_answering import load_qa_chain


class CRUD():
    def __init__(self):
        self.client = chromadb.PersistentClient(path = DB_PATH)
        
    def save_to_db(self, data):
        for item in data:
            collection_name, document, embedding= item['collection_name'], item['document'], item['embedding']

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

            print(f"'{document.page_content}' is added to the collection {collection_name}")
        
        '''
        here might consider checking if the collection exists before using
        get_or_create_collection

        will also need to update this function to async
        '''

    async def retrieve_relevant_history(self, channel_id, query_embedding, top_k=10):
        try:
            # Generate the embedding for the query
            collection_name = f"chat_history_{channel_id}"  # Change from int to str
            print(f"Retrieving collection for channel ID: {collection_name}")

            # Get the collection
            collection = self.client.get_collection(collection_name)
            print(f"Collection retrieved: {collection}")

            # Query the collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )

            for document in results["documents"]:
                print(f"Result: {document}")

            return results

        except Exception as e:
            print(f"Error with retrieving relevant history: {e}")
            return []

    async def save_pdfs(self, file_path, collection_name):
        # Get the files
        try:
            loader = DirectoryLoader(file_path, glob = "*.pdf", show_progress = True)
            docs = loader.load()

        except Exception as e:
            print(f"Error with loading PDFs: {e}")
            return
        

        # split the text 
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = 1000, 
            chunk_overlap = 200
        )

        # get docs, ids, and filenames (for metadata purposes)
        docs = text_splitter.split_documents(docs)
        ids = [str(uuid.uuid4()) for _ in range(len(docs))]

        # remove the file path and extension from the source
        filenames = [doc.metadata['source'].split('/')[-1].split('.')[0] for doc in docs]

        # get the hyperlinks for the pdfs with filenames
        hyperlinks_file = f"{file_path}/hyperlinks.csv"
        urls = read_hyperlinks(hyperlinks_file)
        matched_urls = match_filenames_to_urls(filenames, urls)

        for filename, url in matched_urls.items():
            print(f"{filename}: {url}")

        # save the docs in the collection with collection_name
        collection = self.client.get_or_create_collection(collection_name)
        for doc, id, filename in zip(docs, ids, filenames):
            embedding = await generate_embedding(doc.page_content)
            url = matched_urls.get(filename, "URL not found")
        
            if url:
                source = f"[{filename}]({url})"
            else:
                source = filename

            collection.add(
                ids=[id],
                documents=[doc.page_content],
                embeddings=[embedding],
                metadatas=[{"source": source}]
            )

            print(f"Saved {filename} to collection {collection_name}")
        

