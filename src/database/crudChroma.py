# crudChroma.py
import chromadb, uuid, os, urllib.parse, asyncio
import os
from pathlib import Path


from utlis.config import DB_PATH
from database.modelsChroma import generate_embedding
from services.getPdfs import read_hyperlinks, match_filenames_to_urls
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader

class CRUD():
    def __init__(self):
        self.client = chromadb.PersistentClient(path = DB_PATH)
        
    async def save_to_db(self, data):
        for item in data:
            #added metadata
            collection_name, document, embedding, metadata = item['collection_name'], item['document'], item['embedding'], item['metadata']

            # Change collection_name to type str since it was an int, but has to
            # be a str in order to be used as a collection name
            collection_name = str(collection_name)

            # Note that collection_name is equivalent to channel_id
            collection = await asyncio.to_thread(self.client.get_or_create_collection, collection_name)

            print(f"DEBUG: Metadata for document -> {metadata}")
            if 'id' not in metadata:
                print(f"ERROR: 'id' key is missing in metadata! Skipping...")
                continue  # Skip this document if no ID

            existing_doc = await asyncio.to_thread(collection.get, ids=[metadata["id"]])

            # Don't save duplicates
            if existing_doc and existing_doc["documents"]:
                print(f"Document {metadata['id']} already exists. Skipping...")
                continue  

            await asyncio.to_thread(collection.upsert,
                # Same for id, has to be a str
                ids=[str(metadata['id'])],
                documents=[document.page_content],
                embeddings=[embedding],
                metadatas=[metadata]
            )

            print(f"'{document.page_content}' is added to the collection {collection_name}")

    async def get_data_by_similarity(self, collection_name, query_embedding, top_k=10):
        try:
            # Generate the embedding for the query
            print(f"Retrieving documents for the collection: {collection_name}")

            # Get the collection
            collection = self.client.get_collection(collection_name)
            print(f"Collection retrieved: {collection}")

            # Query the collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )

            return results

        except Exception as e:
            print(f"Error with retrieving relevant history: {e}")
            return []
    
    async def get_data_by_id(self, collection_name, ids):
        # convert ids to str
        ids = [str(id) for id in ids]
        try:
            collection = self.client.get_collection(collection_name)
            results = collection.get(
                ids=ids,
                # where={"style": "style1"}
            )

            return results

        except Exception as e:
            print(f"Error with retrieving data by id: {e}")
            return []
    
    async def save_pdfs(self, pdfs_file_path, category_prefix="course_materials"):
        #pass in directory with pdf folders, and the prefix relates to type.
        print(f"Scanning for PDFs from {pdfs_file_path} ... ")

        #Quick edge case checking.

        data_to_save = []  

        # Check if `pdf_files/` has **subdirectories** (Wei's structure)
        has_subdirectories = any(Path(pdfs_file_path).iterdir())

        # If no subdirectories → Save all PDFs to `course_materials`
        if not has_subdirectories:
            print(f"No subdirectories found! Storing PDFs directly in `course_materials` collection...")
            category_prefix = "course_materials"
            data_to_save.extend(await self._process_pdfs(Path(pdfs_file_path), category_prefix))

        else:
            for category_folder in Path(pdfs_file_path).iterdir():
                # Assuming Wei structure, load pdfs from each sub directroy in pdf directory.
                if category_folder.is_dir():
                    #if directory ... load pdfs
                    category_prefix = category_folder.name

                    for sub_category_folder in category_folder.iterdir():
                        sub_category_name = sub_category_folder.name
                        
                        #Wei wants category_[subcategory] as the collection name
                        collection_name = f"{category_prefix}_[{sub_category_name}]"


                        print(f"Loading PDFs from {category_prefix}, subject: {sub_category_name} ...")
                        #Example, would be loading course_materials/CS 1114

                        data_to_save.extend(await self._process_pdfs(sub_category_folder, collection_name))
                        
        return data_to_save


                    


    async def process_data(self, directory, collection_name):
        try:
            loader = DirectoryLoader(str(directory), glob="*.pdf", show_progress=True)
            docs = loader.load()

            if not docs:
                print(f" No PDFs found in {directory}, skipping...")
                return []

            # Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            docs = text_splitter.split_documents(docs)

            # Generate unique IDs
            ids = [str(uuid.uuid4()) for _ in range(len(docs))]
            for doc, doc_id in zip(docs, ids):
                doc.metadata['id'] = doc_id

            # Extract filenames
            filenames = [doc.metadata['source'].split('/')[-1].split('.')[0] for doc in docs]

            # Match URLs from hyperlinks.csv
            hyperlinks_file = os.path.join(os.path.dirname(__file__), "../services/hyperlinks.csv")
            print(f"Looking for hyperlinks.csv at: {os.path.abspath(hyperlinks_file)}")
            urls = read_hyperlinks(hyperlinks_file)
            matched_urls = match_filenames_to_urls(filenames, urls)

            processed_data = []
            for doc, doc_id, filename in zip(docs, ids, filenames):
                url, text = matched_urls.get(filename, (None, "Description not found"))
                combined_text = f"{text} {doc.page_content}"
                print(f" Processing {filename}...")

                embedding = await generate_embedding(combined_text)

                # Format metadata
                filename = urllib.parse.unquote(filename.replace('_', ' '))
                source = f"[{filename}]({url})" if url else filename

                metadata = {"id": doc_id, "source": source}
                processed_data.append({"collection_name": collection_name, "document": doc, "embedding": embedding, "metadata": metadata})

            return processed_data

        except Exception as e:
            print(f" Error processing PDFs: {e}")
            return []