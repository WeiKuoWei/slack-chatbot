import asyncio
from database.crudChroma import CRUD

crud = CRUD()
collection_name = "course_materials" 
async def check_db():
    results = await crud.get_data_by_id(collection_name, [])  # Get all stored data
    print("Stored documents in ChromaDB:", results)

asyncio.run(check_db())
