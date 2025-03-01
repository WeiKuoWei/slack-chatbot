import asyncio
from database.crudChroma import CRUD

crud = CRUD()
collection_name = "course_materials" 
async def check_db():
    results = await crud.get_data_by_id(collection_name, [])  # Get all stored data
    print("Stored documents in ChromaDB:", results)

async def check_existing():
    crud = CRUD()
    collection_name = "course_materials"
    
    existing_data = await crud.get_data_by_id(collection_name, [])
    print(f"Found {len(existing_data['ids'])} documents in ChromaDB.")
    # Print some metadata to verify uniqueness
    for i in range(min(5, len(existing_data["metadatas"]))):  # Limit to 5 sample docs
        print(f"📄 {existing_data['metadatas'][i]}")

asyncio.run(check_existing())
async def main():
    await asyncio.gather(check_db(), check_existing())

if __name__ == "__main__":
    asyncio.run(main())