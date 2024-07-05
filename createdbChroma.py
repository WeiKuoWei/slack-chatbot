import chromadb, os
from dotenv import load_dotenv

# load local functions
from crudChroma import CRUD

load_dotenv()

# create your own DB_PATH in a .env file to store chromadb data
DB_PATH = os.getenv("DB_PATH") 

def main():
    # Connect to ChromaDB  
    crud = CRUD()
    crud.create_collection("team_ids")

    # load the current workspace_list.json file into the team_ids collection
    
    '''
    if we have to reset the database, all other collections will be
    initialized here in the future
    '''

if __name__ == '__main__':
    main()

'''
Note that only the team_ids collection is created in createdbChroma.py. This is
because all the other collections are 1-to-many relationships and are created in
the appChroma.py file.
'''
