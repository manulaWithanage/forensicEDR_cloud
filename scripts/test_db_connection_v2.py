import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import certifi

load_dotenv()

async def test_connection():
    uri = os.getenv("MONGODB_URI")
    print(f"Testing connection to: {uri.split('@')[-1]}") # Hide credentials
    
    try:
        client = AsyncIOMotorClient(uri, tlsCAFile=certifi.where())
        await client.admin.command('ping')
        print("✅ Connection Successful!")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
