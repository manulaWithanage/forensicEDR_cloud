"""MongoDB connection and schema setup"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, GEOSPHERE
from pymongo.errors import CollectionInvalid
from .config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database manager"""
    
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None


# Global database instance
database = Database()


async def connect_to_mongodb():
    """Connect to MongoDB and initialize database"""
    logger.info("Connecting to MongoDB...")
    database.client = AsyncIOMotorClient(settings.MONGODB_URI)
    database.db = database.client.forensic_edr
    logger.info("✅ Connected to MongoDB")


async def close_mongodb_connection():
    """Close MongoDB connection"""
    logger.info("Closing MongoDB connection...")
    database.client.close()
    logger.info("✅ MongoDB connection closed")


async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    return database.db


async def check_database_health() -> dict:
    """Check MongoDB connection health"""
    try:
        # Ping the database
        await database.db.command('ping')
        
        # Get server info
        server_info = await database.db.command('serverStatus')
        
        return {
            'status': 'connected',
            'database': 'forensic_edr',
            'version': server_info.get('version', 'unknown'),
            'uptime': server_info.get('uptime', 0)
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


async def create_collections():
    """Create MongoDB collections with validation schemas"""
    db = database.db
    
    # Collection 1: crash_events
    try:
        await db.create_collection(
            "crash_events",
            validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["event_id", "timestamp", "crash_event", "location"],
                    "properties": {
                        "event_id": {
                            "bsonType": "string",
                            "description": "Unique event identifier - required"
                        },
                        "timestamp": {
                            "bsonType": "date",
                            "description": "Event timestamp - required"
                        },
                        "crash_event": {
                            "bsonType": "string",
                            "description": "Crash event description - required"
                        },
                        "crash_type": {
                            "enum": ["frontal_impact_collision", "side_impact_collision", 
                                   "rear_end_collision", "rollover_event"],
                            "description": "Type of crash"
                        },
                        "severity": {
                            "enum": ["minor", "moderate", "severe"],
                            "description": "Crash severity level"
                        },
                        "location": {
                            "bsonType": "object",
                            "required": ["type", "coordinates"],
                            "properties": {
                                "type": {
                                    "enum": ["Point"]
                                },
                                "coordinates": {
                                    "bsonType": ["array"],
                                    "minItems": 2,
                                    "maxItems": 2
                                }
                            }
                        }
                    }
                }
            }
        )
        logger.info("✅ Created collection: crash_events")
    except CollectionInvalid:
        logger.info("Collection crash_events already exists")
    
    # Collection 2: raw_telemetry
    try:
        await db.create_collection("raw_telemetry")
        logger.info("✅ Created collection: raw_telemetry")
    except CollectionInvalid:
        logger.info("Collection raw_telemetry already exists")
    
    # Collection 3: evidence_custody_logs
    try:
        await db.create_collection(
            "evidence_custody_logs",
            validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["entry_id", "timestamp", "event_id", "action", 
                               "actor", "location", "previous_hash", "entry_hash"],
                    "properties": {
                        "entry_id": {
                            "bsonType": "string",
                            "description": "Unique custody entry identifier - required"
                        },
                        "action": {
                            "enum": ["EVIDENCE_COLLECTION", "TRANSFER", "ACCESS", 
                                   "VERIFICATION", "MODIFICATION", "EXPORT", "DELETION"],
                            "description": "Type of custody action - required"
                        },
                        "previous_hash": {
                            "bsonType": "string",
                            "description": "Hash of previous entry in chain - required"
                        },
                        "entry_hash": {
                            "bsonType": "string",
                            "description": "SHA-256 hash of this entry - required"
                        }
                    }
                }
            }
        )
        logger.info("✅ Created collection: evidence_custody_logs")
    except CollectionInvalid:
        logger.info("Collection evidence_custody_logs already exists")
    
    # Collection 4: cached_reports (for dashboard)
    try:
        await db.create_collection(
            "cached_reports",
            validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["report_id", "report_type", "generated_at"],
                    "properties": {
                        "report_id": {
                            "bsonType": "string",
                            "description": "Unique report identifier"
                        },
                        "report_type": {
                            "enum": ["severity", "timeline", "geographic", "crash_type", "impact"],
                            "description": "Type of report"
                        },
                        "generated_at": {
                            "bsonType": "date",
                            "description": "Report generation timestamp"
                        }
                    }
                }
            }
        )
        logger.info("✅ Created collection: cached_reports")
    except CollectionInvalid:
        logger.info("Collection cached_reports already exists")


async def create_indexes():
    """Create all required MongoDB indexes"""
    db = database.db
    
    # Indexes for crash_events
    await db.crash_events.create_index([("event_id", ASCENDING)], unique=True)
    await db.crash_events.create_index([("timestamp", DESCENDING)])
    await db.crash_events.create_index([("location", GEOSPHERE)])  # 2dsphere index for geospatial queries
    await db.crash_events.create_index([("metadata.device_id", ASCENDING)])
    await db.crash_events.create_index([("severity", ASCENDING), ("timestamp", DESCENDING)])
    await db.crash_events.create_index([("crash_type", ASCENDING)])
    logger.info("✅ Created indexes for crash_events (including 2dsphere)")
    
    # Indexes for raw_telemetry
    await db.raw_telemetry.create_index([("event_id", ASCENDING)])
    await db.raw_telemetry.create_index([("timestamp", DESCENDING)])
    logger.info("✅ Created indexes for raw_telemetry")
    
    # Indexes for evidence_custody_logs
    await db.evidence_custody_logs.create_index([("entry_id", ASCENDING)], unique=True)
    await db.evidence_custody_logs.create_index([("entry_hash", ASCENDING)], unique=True)
    await db.evidence_custody_logs.create_index([("event_id", ASCENDING)])
    await db.evidence_custody_logs.create_index([("timestamp", DESCENDING)])
    await db.evidence_custody_logs.create_index([("action", ASCENDING), ("timestamp", DESCENDING)])
    await db.evidence_custody_logs.create_index([("actor", ASCENDING), ("timestamp", DESCENDING)])
    await db.evidence_custody_logs.create_index([("previous_hash", ASCENDING)])
    await db.evidence_custody_logs.create_index([("event_id", ASCENDING), ("timestamp", ASCENDING)])
    logger.info("✅ Created indexes for evidence_custody_logs")
    
    # Indexes for cached_reports
    await db.cached_reports.create_index([("report_id", ASCENDING)], unique=True)
    await db.cached_reports.create_index([("report_type", ASCENDING)])
    await db.cached_reports.create_index([("generated_at", DESCENDING)])
    await db.cached_reports.create_index([("generated_at", DESCENDING)], expireAfterSeconds=3600)  # Auto-delete after 1 hour
    logger.info("✅ Created indexes for cached_reports (with TTL)")


async def initialize_database():
    """Initialize database with collections and indexes"""
    await connect_to_mongodb()
    await create_collections()
    await create_indexes()
    logger.info("✅ Database initialization complete")
