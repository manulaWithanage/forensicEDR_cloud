"""Sample evidence upload script - generates encrypted crash data and uploads to API"""
import sys
import os
import json
import httpx
import asyncio
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.encryption import encrypt_evidence
from app.config import settings


def generate_sample_crash_data():
    """Generate sample crash event data"""
    crash_data = {
        "event_id": f"event_{datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')}",
        "timestamp": datetime.utcnow().isoformat(),
        "crash_event": "COLLISION: Test crash for upload verification",
        "crash_type": "frontal_impact_collision",
        "severity": "moderate",
        "location": {
            "latitude": 6.9271,
            "longitude": 79.8612,
            "address": "Colombo Fort, Sri Lanka"
        },
        "raw_data": [
            {
                "timestamp": "2024-12-01T00:15:29.000000",
                "speed": 65.5,
                "rpm": 2800,
                "throttle_pos": 0,
                "engine_load": 50.0,
                "coolant_temp": 87.0,
                "fuel_level": 60.0,
                "latitude": 6.9270,
                "longitude": 79.8610,
                "accel_x": -4.5,
                "accel_y": -0.2,
                "accel_z": -1.0,
                "airbag_status": "False",
                "power_status": "OK",
                "tilt": -1.5,
                "total_acceleration": 4.62,
                "angular_acceleration": 0.5,
                "hard_brake_event": 1,
                "event": "Hard braking"
            },
            {
                "timestamp": "2024-12-01T00:15:30.000000",
                "speed": 0.0,
                "rpm": 0,
                "throttle_pos": 0,
                "engine_load": 0,
                "coolant_temp": 87.0,
                "fuel_level": 60.0,
                "latitude": 6.9271,
                "longitude": 79.8612,
                "accel_x": -10.5,
                "accel_y": -0.6,
                "accel_z": -2.5,
                "airbag_status": "True",
                "power_status": "OK",
                "tilt": 2.8,
                "total_acceleration": 10.85,
                "angular_acceleration": 1.8,
                "hard_brake_event": 1,
                "event": "COLLISION: Frontal impact"
            }
        ],
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
            "device_id": "EDR_TEST_DEVICE",
            "firmware_version": "1.0.0",
            "buffer_seconds": 60,
            "detection_algorithm": "rule_based_v1"
        }
    }
    
    return crash_data


async def upload_to_api(encrypted_file_path: str, api_url: str = "http://localhost:8000"):
    """Upload encrypted evidence file to API"""
    upload_url = f"{api_url}/api/v1/upload/evidence"
    
    print(f"\n📤 Uploading to: {upload_url}")
    
    try:
        async with httpx.AsyncClient() as client:
            with open(encrypted_file_path, 'rb') as f:
                files = {'file': ('test_evidence.bin', f, 'application/octet-stream')}
                
                response = await client.post(upload_url, files=files, timeout=30.0)
                
                if response.status_code == 200:
                    result = response.json()
                    print("\n✅ Upload successful!")
                    print(f"   Event ID: {result.get('event_id')}")
                    print(f"   Timestamp: {result.get('timestamp')}")
                    print(f"   Status: {result.get('status')}")
                    return True
                else:
                    print(f"\n❌ Upload failed: HTTP {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False
                    
    except httpx.ConnectError:
        print(f"\n❌ Cannot connect to API at {api_url}")
        print("   Make sure the server is running: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"\n❌ Upload error: {e}")
        return False


async def main():
    """Main function"""
    print("=" * 60)
    print("ForensicEDR Sample Evidence Upload")
    print("=" * 60)
    
    # Generate crash data
    print("\n📊 Generating sample crash data...")
    crash_data = generate_sample_crash_data()
    print(f"   Event ID: {crash_data['event_id']}")
    print(f"   Crash Type: {crash_data['crash_type']}")
    print(f"   Severity: {crash_data['severity']}")
    
    # Encrypt data
    print("\n🔐 Encrypting evidence...")
    try:
        encrypted_data = encrypt_evidence(crash_data)
        print(f"   Encrypted size: {len(encrypted_data)} bytes")
    except Exception as e:
        print(f"❌ Encryption failed: {e}")
        print("\nMake sure .env file exists with AES_ENCRYPTION_KEY")
        print("Generate key: python -c \"import secrets; print(secrets.token_hex(32))\"")
        sys.exit(1)
    
    # Save to file
    encrypted_file = "test_evidence.bin"
    with open(encrypted_file, 'wb') as f:
        f.write(encrypted_data)
    print(f"   ✅ Saved to: {encrypted_file}")
    
    # Upload to API
    success = await upload_to_api(encrypted_file)
    
    # Cleanup
    if os.path.exists(encrypted_file):
        os.remove(encrypted_file)
        print(f"\n🗑️  Cleaned up temporary file")
    
    if success:
        print("\n" + "=" * 60)
        print("✅ TEST COMPLETE - Evidence uploaded successfully!")
        print("=" * 60)
        print("\n📝 Next steps:")
        print("   - View crashes: http://localhost:8000/api/v1/crashes")
        print("   - Generate report: http://localhost:8000/api/v1/reports/generate?report_type=severity")
        print("   - Check custody: http://localhost:8000/api/v1/custody/{event_id}")
        print()
    else:
        print("\n⚠️  Upload failed - check the errors above")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
