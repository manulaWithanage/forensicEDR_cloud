import asyncio
import os
import json
import sys
import httpx
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.encryption import encrypt_evidence
import hashlib

load_dotenv()

# Configuration
API_URL = "http://localhost:8001/api/v1/upload/evidence" # Using 8001 to match current running server
NUM_RECORDS = 15

# Sample Data Pools
CRASH_TYPES = ["frontal_impact_collision", "side_impact_collision", "rear_end_collision", "rollover_event"]
SEVERITIES = ["minor", "moderate", "severe"]
LOCATIONS = [
    {"lat": 6.9271, "lon": 79.8612, "addr": "Colombo 01, Sri Lanka"},
    {"lat": 6.9010, "lon": 79.8549, "addr": "Bambalapitiya, Colombo"},
    {"lat": 6.9147, "lon": 79.8778, "addr": "Borella, Colombo"},
    {"lat": 6.8649, "lon": 79.8997, "addr": "Nugegoda, Sri Lanka"},
    {"lat": 6.9319, "lon": 79.8478, "addr": "Pettah, Colombo"},
    {"lat": 6.8404, "lon": 79.8712, "addr": "Dehiwala-Mount Lavinia"},
]

def calculate_hash(entry):
    """Generate SHA-256 hash of custody entry"""
    entry_for_hash = dict(entry)
    entry_for_hash.pop('entry_hash', None)
    entry_for_hash.pop('_id', None)
    entry_for_hash.pop('created_at', None)
    entry_for_hash.pop('verified', None)
    
    if 'timestamp' in entry_for_hash and isinstance(entry_for_hash['timestamp'], datetime):
        entry_for_hash['timestamp'] = entry_for_hash['timestamp'].isoformat()
    
    entry_json = json.dumps(entry_for_hash, sort_keys=True)
    hash_obj = hashlib.sha256(entry_json.encode('utf-8'))
    return hash_obj.hexdigest()

async def upload_single_record(index):
    # Randomize Data
    timestamp = (datetime.utcnow() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))).isoformat()
    event_id = f"evt_{datetime.utcnow().strftime('%Y%m%d')}_{index:03d}_{random.randint(1000,9999)}"
    crash_type = random.choice(CRASH_TYPES)
    severity = random.choice(SEVERITIES)
    loc = random.choice(LOCATIONS)
    
    # Jitter location slightly
    lat = loc["lat"] + random.uniform(-0.005, 0.005)
    lon = loc["lon"] + random.uniform(-0.005, 0.005)

    crash_data = {
        "event_id": event_id,
        "timestamp": timestamp,
        "crash_event": f"Simulated {crash_type.replace('_', ' ')}",
        "crash_type": crash_type,
        "severity": severity,
        "location": {
            "latitude": lat,
            "longitude": lon,
            "address": loc["addr"]
        },
        "calculated_values": {
            "speed_now": 0.0,
            "speed_previous": random.uniform(30.0, 120.0),
            "deceleration": random.uniform(-80.0, -20.0),
            "impact_force_g": random.uniform(0.5, 5.0),
            "airbag_status": "True" if severity != "minor" else "False"
        },
        "metadata": {
            "device_id": f"EDR_UNIT_{random.randint(1, 5)}",
            "firmware_version": "2.1.0"
        }
    }

    # Encrypt
    encrypted_data = encrypt_evidence(crash_data)

    # Create Custody Log
    edge_log = {
        "entry_id": f"log_{event_id}_edge",
        "timestamp": timestamp,
        "event_id": event_id,
        "action": "EVIDENCE_COLLECTION",
        "actor": "EDGE_SIMULATOR",
        "location": "VEHICLE_SIM",
        "details": {"source": "populate_db_script"},
        "previous_hash": "0" * 64,
        "hash_algorithm": "SHA-256"
    }
    edge_log["entry_hash"] = calculate_hash(edge_log)
    edge_log_json = json.dumps(edge_log)

    # Upload
    async with httpx.AsyncClient() as client:
        files = {'file': (f'{event_id}.bin', encrypted_data, 'application/octet-stream')}
        data = {'custody_log': edge_log_json}
        
        try:
            res = await client.post(API_URL, files=files, data=data, timeout=10.0)
            if res.status_code == 200:
                print(f"✅ Uploaded {event_id} ({severity})")
            else:
                print(f"❌ Failed {event_id}: {res.text}")
        except Exception as e:
            print(f"❌ Error {event_id}: {e}")

async def main():
    print(f"🚀 Starting population of {NUM_RECORDS} records to {API_URL}...")
    
    tasks = []
    for i in range(NUM_RECORDS):
        tasks.append(upload_single_record(i))
        # Add small delay to prevent overwhelming if running locally
        await asyncio.sleep(0.1)
    
    await asyncio.gather(*tasks)
    print("\n✨ Population complete!")

if __name__ == "__main__":
    asyncio.run(main())
