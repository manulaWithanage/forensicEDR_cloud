import asyncio
import os
import json
import sys
import httpx
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.encryption import encrypt_evidence
import hashlib

load_dotenv()

def calculate_hash(entry):
    """Generate SHA-256 hash of custody entry (standalone for testing)"""
    # Create a copy without the entry_hash and _id fields
    entry_for_hash = dict(entry)
    entry_for_hash.pop('entry_hash', None)
    entry_for_hash.pop('_id', None)
    entry_for_hash.pop('created_at', None)
    entry_for_hash.pop('verified', None)
    
    # Convert datetime objects to ISO strings
    if 'timestamp' in entry_for_hash and isinstance(entry_for_hash['timestamp'], datetime):
        entry_for_hash['timestamp'] = entry_for_hash['timestamp'].isoformat()
    
    # Sort keys for deterministic JSON
    entry_json = json.dumps(entry_for_hash, sort_keys=True)
    
    # Generate SHA-256 hash
    hash_obj = hashlib.sha256(entry_json.encode('utf-8'))
    return hash_obj.hexdigest()

async def test_upload_v2():
    print("=" * 60)
    print("Testing Upload V2 (With Custody Log)")
    print("=" * 60)

    # 1. Generate Crash Data (New Format)
    event_id = f"event_v2_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    timestamp = datetime.utcnow().isoformat()
    
    crash_data = {
        "event_id": event_id,
        "timestamp": timestamp,
        "crash_event": "COLLISION: V2 Test",
        "crash_type": "frontal_impact_collision",
        "severity": "severe",
        "location": {
            "latitude": 6.9271,
            "longitude": 79.8612,
            "address": "Colombo, Sri Lanka"
        },
        "calculated_values": {
            "speed_now": 0.0,
            "speed_previous": 65.5,
            "deceleration": -65.5,
            "total_acceleration": 10.85,
            "angular_acceleration": 1.8,
            "hard_brake_event": "Yes",
            "airbag_status": "True",
            "power_status": "OK",
            "tilt": 2.8,
            "impact_force_g": 1.11
        },
        "metadata": {
            "device_id": "EDR_TEST_V2",
            "firmware_version": "2.0.0"
        }
    }
    
    # 2. Encrypt Data
    print("\n🔐 Encrypting evidence...")
    encrypted_data = encrypt_evidence(crash_data)
    
    # 3. Create Edge Custody Log
    print("📝 Creating edge custody log...")
    edge_log = {
        "entry_id": f"log_{event_id}_001",
        "timestamp": timestamp,
        "event_id": event_id,
        "action": "EVIDENCE_COLLECTION",
        "actor": "EDGE_DEVICE_V2",
        "location": "VEHICLE_LKA_123",
        "details": {"note": "Generated at edge"},
        "previous_hash": "0" * 64, # Genesis
        "hash_algorithm": "SHA-256"
    }
    # Calculate hash manually for test
    edge_log["entry_hash"] = calculate_hash(edge_log)
    
    edge_log_json = json.dumps(edge_log)
    
    # 4. Upload
    url = "http://localhost:8001/api/v1/upload/evidence"
    health_url = "http://localhost:8001/health"
    
    async with httpx.AsyncClient() as client:
        # Check health first
        try:
            print(f"🏥 Checking health at {health_url}...")
            health_res = await client.get(health_url, timeout=5.0)
            print(f"   Status: {health_res.status_code}")
        except Exception as e:
            print(f"   ❌ Health check failed: {repr(e)}")
            return

        print(f"\n📤 Uploading to {url}...")
        # Prepare multipart form data
        files = {'file': ('evidence_v2.bin', encrypted_data, 'application/octet-stream')}
        data = {'custody_log': edge_log_json}
        
        try:
            response = await client.post(url, files=files, data=data, timeout=30.0)
            
            if response.status_code == 200:
                print("\n✅ Upload Successful!")
                print(response.json())
                
                # 5. Verify Custody Chain via API
                print("\n🔍 Verifying Custody Chain...")
                custody_url = f"http://localhost:8000/api/v1/custody/{event_id}"
                custody_res = await client.get(custody_url)
                
                if custody_res.status_code == 200:
                    chain_data = custody_res.json()
                    chain = chain_data['chain']
                    print(f"   Chain Length: {len(chain)} (Expected 2)")
                    
                    if len(chain) >= 2:
                        print(f"   Entry 1 Actor: {chain[0]['actor']} (Expected EDGE_DEVICE_V2)")
                        print(f"   Entry 2 Actor: {chain[1]['actor']} (Expected CLOUD_API)")
                        
                        # Verify linking
                        if chain[1]['previous_hash'] == chain[0]['entry_hash']:
                            print("   ✅ Chain is properly linked!")
                        else:
                            print("   ❌ Chain linking failed!")
                    else:
                        print("   ❌ Missing chain entries!")
                else:
                    print("   ❌ Failed to fetch custody chain")
                    
            else:
                print(f"\n❌ Upload Failed: {response.text}")
                
        except Exception as e:
            print(f"\n❌ Error: {repr(e)}")

if __name__ == "__main__":
    asyncio.run(test_upload_v2())
