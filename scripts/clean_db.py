"""
Clean MongoDB Database - Remove all documents from collections
Preserves collection structure and indexes
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import certifi

load_dotenv()

async def clean_database():
    """Remove all documents from all collections"""
    uri = os.getenv("MONGODB_URI")
    
    print("🧹 Starting MongoDB cleanup...")
    print(f"   Connecting to: {uri.split('@')[-1]}")
    
    try:
        client = AsyncIOMotorClient(uri, tlsCAFile=certifi.where())
        db = client.forensic_edr
        
        # Get all collection names
        collections = await db.list_collection_names()
        
        print(f"\n📋 Found {len(collections)} collections")
        
        for collection_name in collections:
            # Count before deletion
            count_before = await db[collection_name].count_documents({})
            
            # Delete all documents
            result = await db[collection_name].delete_many({})
            
            print(f"   ✅ {collection_name}: Deleted {result.deleted_count} documents (had {count_before})")
        
        print("\n✨ Database cleaned successfully!")
        print("   Collections and indexes are preserved.")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(clean_database())
