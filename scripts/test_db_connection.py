import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import certifi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

async def test_connection():
    print(f"Testing connection to MongoDB...")
    print(f"Certifi path: {certifi.where()}")
    
    try:
        # Try with certifi
        client = AsyncIOMotorClient(
            MONGODB_URI,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000
        )
        print("Attempting to ping database...")
        await client.admin.command('ping')
        print("✅ Connection successful with certifi!")
        
    except Exception as e:
        print(f"❌ Connection failed with certifi: {e}")
        
        print("\nAttempting fallback: tlsAllowInvalidCertificates=True (INSECURE - FOR TESTING ONLY)")
        try:
            client_insecure = AsyncIOMotorClient(
                MONGODB_URI,
                tlsAllowInvalidCertificates=True,
                serverSelectionTimeoutMS=5000
            )
            await client_insecure.admin.command('ping')
            print("⚠️ Connection successful with tlsAllowInvalidCertificates=True")
            print("This indicates a certificate verification issue.")
        except Exception as e2:
            print(f"❌ Connection failed even with invalid certs allowed: {e2}")

if __name__ == "__main__":
    asyncio.run(test_connection())
