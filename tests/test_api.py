"""Pytest test suite for all 7 API endpoints"""
import py test
import httpx
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.encryption import encrypt_evidence


# Test configuration
API_BASE_URL = "http://localhost:8000"


@pytest.fixture
def test_crash_data():
    """Generate test crash data"""
    return {
        "event_id": f"test_event_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "timestamp": datetime.utcnow().isoformat(),
        "crash_event": "TEST: Automated test crash",
        "crash_type": "frontal_impact_collision",
        "severity": "moderate",
        "location": {
            "latitude": 6.9271,
            "longitude": 79.8612,
            "address": "Test Location"
        },
        "raw_data": [],
        "calculated_values": {
            "speed_now": 0.0,
            "speed_previous": 50.0,
            "deceleration": -50.0,
            "total_acceleration": 8.5,
            "angular_acceleration": 1.5,
            "hard_brake_event": "Yes",
            "airbag_status": "True",
            "power_status": "OK",
            "tilt": 2.0,
            "impact_force_g": 0.87
        },
        "metadata": {
            "device_id": "TEST_DEVICE",
            "firmware_version": "1.0.0",
            "buffer_seconds": 60,
            "detection_algorithm": "rule_based_v1"
        }
    }


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test 1: GET /health"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "database" in data
        print("✅ Test passed: Health check endpoint")


@pytest.mark.asyncio
async def test_upload_evidence(test_crash_data):
    """Test 2: POST /api/v1/upload/evidence"""
    # Encrypt test data
    encrypted_data = encrypt_evidence(test_crash_data)
    
    # Create file-like object
    files = {'file': ('test_crash.bin', encrypted_data, 'application/octet-stream')}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/upload/evidence",
            files=files,
            timeout=30.0
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "event_id" in data
        print(f"✅ Test passed: Evidence upload (Event ID: {data['event_id']})")
        
        return data["event_id"]


@pytest.mark.asyncio
async def test_get_crashes():
    """Test 3: GET /api/v1/crashes"""
    async with httpx.AsyncClient() as client:
        # Test without filters
        response = await client.get(f"{API_BASE_URL}/api/v1/crashes")
        assert response.status_code == 200
        crashes = response.json()
        assert isinstance(crashes, list)
        
        # Test with severity filter
        response = await client.get(
            f"{API_BASE_URL}/api/v1/crashes?severity=severe&limit=10"
        )
        assert response.status_code == 200
        print("✅ Test passed: Get crashes with filters")


@pytest.mark.asyncio
async def test_get_crash_by_id():
    """Test4: GET /api/v1/crashes/{event_id}"""
    # Use a known event ID from setup
    test_event_id = "event_2024-11-30_18-15-32"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/v1/crashes/{test_event_id}"
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "crash_event" in data
            assert "telemetry" in data
            assert "custody_chain" in data
            print(f"✅ Test passed: Get crash by ID ({test_event_id})")
        else:
            print(f"⚠️  Event {test_event_id} not found (may need to run setup_db.py)")


@pytest.mark.asyncio
async def test_get_crashes_nearby():
    """Test 5: GET /api/v1/crashes/nearby"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/v1/crashes/nearby",
            params={
                "latitude": 6.9271,
                "longitude": 79.8612,
                "radius_km": 10
            }
        )
        
        assert response.status_code == 200
        crashes = response.json()
        assert isinstance(crashes, list)
        print(f"✅ Test passed: Geospatial nearby search (found {len(crashes)} crashes)")


@pytest.mark.asyncio
async def test_generate_reports():
    """Test 6: GET /api/v1/reports/generate"""
    report_types = ["severity", "timeline", "geographic", "crash_type", "impact"]
    
    for report_type in report_types:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/v1/reports/generate",
                params={
                    "report_type": report_type,
                    "format": "json"
                },
                timeout=30.0
            )
            
            assert response.status_code in [200, 400]  # 400 if no data available
            if response.status_code == 200:
                data = response.json()
                assert "report_type" in data
                assert "data" in data
                print(f"✅ Test passed: Generate {report_type} report")


@pytest.mark.asyncio
async def test_get_custody_chain():
    """Test 7: GET /api/v1/custody/{event_id}"""
    # Use a known event ID from setup
    test_event_id = "event_2024-11-30_18-15-32"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/v1/custody/{test_event_id}"
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "chain" in data
            assert "chain_valid" in data
            assert "verification_details" in data
            assert data["chain_valid"] == True
            print(f"✅ Test passed: Custody chain verification (valid: {data['chain_valid']})")
        else:
            print(f"⚠️  No custody chain for {test_event_id} (may need to run setup_db.py)")


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test: GET / (root)"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "endpoints" in data
        print("✅ Test passed: Root endpoint")


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
