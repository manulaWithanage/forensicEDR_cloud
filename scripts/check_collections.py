import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import certifi
from dotenv import load_dotenv

load_dotenv()

async def list_collections():
    client = AsyncIOMotorClient(
        os.getenv("MONGODB_URI"),
        tlsCAFile=certifi.where()
    )
    db = client.forensic_edr
    collections = await db.list_collection_names()
    print(f"Collections: {collections}")
    
    if "cached_reports" in collections:
        print("✅ cached_reports collection exists!")
    else:
        print("❌ cached_reports collection MISSING!")

if __name__ == "__main__":
    asyncio.run(list_collections())
