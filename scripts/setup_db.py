"""Database initialization script - creates collections, indexes, and sample data"""
import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import initialize_database, database
from app.config import settings


async def insert_sample_data():
    """Insert sample crash data for testing"""
    db = database.db
    
    print("\n📊 Inserting sample crash data...")
    
    # Sample crash event 1: Severe frontal impact
    sample_crash_1 = {
        "event_id": "event_2024-11-30_18-15-32",
        "timestamp": datetime(2024, 11, 30, 18, 15, 32, 456789),
        "crash_event": "COLLISION: Airbag deployment detected (CRASH)",
        "crash_type": "frontal_impact_collision",
        "severity": "severe",
        "location": {
            "type": "Point",
            "coordinates": [79.8625, 6.9284],  # [longitude, latitude]
            "address": "Colombo, Sri Lanka"
        },
        "calculated_values": {
            "speed_now": 0.0,
            "speed_previous": 35.0,
            "deceleration": -35.0,
            "total_acceleration": 13.15,
            "angular_acceleration": 2.5,
            "hard_brake_event": "Yes",
            "airbag_status": "True",
            "power_status": "FAIL",
            "tilt": 3.2,
            "impact_force_g": 1.34
        },
        "metadata": {
            "device_id": "EDR_DEVICE_001",
            "firmware_version": "1.0.0",
            "buffer_seconds": 60,
            "detection_algorithm": "rule_based_v1"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Sample crash event 2: Moderate side impact
    sample_crash_2 = {
        "event_id": "event_2024-11-30_14-22-18",
        "timestamp": datetime(2024, 11, 30, 14, 22, 18, 123456),
        "crash_event": "COLLISION: Crash impact detected: 11.25 m/s^2",
        "crash_type": "side_impact_collision",
        "severity": "moderate",
        "location": {
            "type": "Point",
            "coordinates": [79.8635, 6.9295],
            "address": "Galle Road, Colombo 03"
        },
        "calculated_values": {
            "speed_now": 19.92,
            "speed_previous": 49.8,
            "deceleration": -29.88,
            "total_acceleration": 11.25,
            "angular_acceleration": 14.2,
            "hard_brake_event": "Yes",
            "airbag_status": "True",
            "power_status": "OK",
            "tilt": 15.0,
            "impact_force_g": 1.15
        },
        "metadata": {
            "device_id": "EDR_DEVICE_002",
            "firmware_version": "1.0.0",
            "buffer_seconds": 60,
            "detection_algorithm": "rule_based_v1"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Sample crash event 3: Minor rear-end
    sample_crash_3 = {
        "event_id": "event_2024-11-30_16-30-45",
        "timestamp": datetime(2024, 11, 30, 16, 30, 45, 345678),
        "crash_event": "COLLISION: Crash likely: Multiple sensor triggers",
        "crash_type": "rear_end_collision",
        "severity": "minor",
        "location": {
            "type": "Point",
            "coordinates": [79.8618, 6.9278],
            "address": "Duplication Road, Colombo"
        },
        "calculated_values": {
            "speed_now": 12.0,
            "speed_previous": 24.0,
            "deceleration": -12.0,
            "total_acceleration": 3.53,
            "angular_acceleration": 3.0,
            "hard_brake_event": "Yes",
            "airbag_status": "False",
            "power_status": "OK",
            "tilt": -4.8,
            "impact_force_g": 0.36
        },
        "metadata": {
            "device_id": "EDR_DEVICE_003",
            "firmware_version": "1.0.0",
            "buffer_seconds": 60,
            "detection_algorithm": "rule_based_v1"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    try:
        # Insert crash events
        await db.crash_events.insert_many([sample_crash_1, sample_crash_2, sample_crash_3])
        print("✅ Inserted 3 sample crash events")
        
        # Insert sample custody log
        from app.custody_chain import CustodyChainManager
        custody_manager = CustodyChainManager(db)
        
        await custody_manager.add_custody_entry(
            event_id="event_2024-11-30_18-15-32",
            action="EVIDENCE_COLLECTION",
            actor="CRASH_DETECTION_SYSTEM",
            location="EDGE_DEVICE",
            details={
                "metadata": {
                    "timestamp": "2024-11-30T18:15:32",
                    "gps_location": "6.9284, 79.8625",
                    "vehicle_id": "LKA-123-4567",
                    "crash_type": "frontal_impact_collision",
                    "severity": "severe"
                }
            }
        )
        print("✅ Created sample custody log entry")
        
    except Exception as e:
        print(f"⚠️  Sample data may already exist or error occurred: {e}")


async def verify_indexes():
    """Verify that all indexes were created correctly"""
    db = database.db
    
    print("\n🔍 Verifying indexes...")
    
    # Check crash_events indexes
    crash_indexes = await db.crash_events.index_information()
    print("\n📋 crash_events indexes:")
    for idx_name, idx_info in crash_indexes.items():
        print(f"  - {idx_name}: {idx_info.get('key', [])}")
    
    # Verify 2dsphere index exists
    has_geospatial = any('2dsphere' in str(idx.get('key', [])) for idx in crash_indexes.values())
    if has_geospatial:
        print("  ✅ 2dsphere geospatial index found!")
    else:
        print("  ⚠️  WARNING: 2dsphere index not found!")
    
    # Check custody logs indexes
    custody_indexes = await db.evidence_custody_logs.index_information()
    print("\n📋 evidence_custody_logs indexes:")
    for idx_name, idx_info in custody_indexes.items():
        print(f"  - {idx_name}: {idx_info.get('key', [])}")
    
    # Check telemetry indexes
    telemetry_indexes = await db.raw_telemetry.index_information()
    print("\n📋 raw_telemetry indexes:")
    for idx_name, idx_info in telemetry_indexes.items():
        print(f"  - {idx_name}: {idx_info.get('key', [])}")


async def main():
    """Main setup function"""
    print("=" * 60)
    print("ForensicEDR Database Setup")
    print("=" * 60)
    
    print(f"\n🔌 Connecting to MongoDB...")
    print(f"   URI: {settings.MONGODB_URI[:30]}...")
    
    try:
        # Initialize database
        await initialize_database()
        
        # Insert sample data
        await insert_sample_data()
        
        # Verify indexes
        await verify_indexes()
        
        print("\n" + "=" * 60)
        print("✅ DATABASE SETUP COMPLETE!")
        print("=" * 60)
        print("\n📝 Next steps:")
        print("   1. Run the server: uvicorn app.main:app --reload")
        print("   2. Visit docs: http://localhost:8000/docs")
        print("   3. Test upload: python scripts/sample_upload.py")
        print()
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Close connection
        from app.database import close_mongodb_connection
        await close_mongodb_connection()


if __name__ == "__main__":
    asyncio.run(main())
