import chromadb, os
from dotenv import load_dotenv

load_dotenv()

# create your own DB_PATH in a .env file to store chromadb data
DB_PATH = os.getenv("DB_PATH") 

def main():
    # Connect to ChromaDB
    client = chromadb.PersistentClient(path=DB_PATH)
    client.get_or_create_collection(name = "team_ids")
    print("team_ids collection created in ChromaDB")

    # load the current workspace_list.json file into the team_ids collection

    # if we have to reset the database, all other collections will be
    # initialized here in the future

if __name__ == '__main__':
    main()

'''
Note that only the team_ids collection is created in createdbChroma.py. This is
because all the other collections are 1-to-many relationships and are created in
the appChroma.py file.
'''
