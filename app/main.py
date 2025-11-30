"""FastAPI application with 7 endpoints for ForensicEDR Cloud Backend"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Optional, List
import logging
import json

from .config import settings
from .database import (
    connect_to_mongodb,
    close_mongodb_connection,
    get_database,
    check_database_health
)
from .custody_chain import CustodyChainManager
from .report_generator import ReportGenerator
from .encryption import decrypt_evidence
from .models import (
    UploadResponse,
    HealthResponse,
    CrashQueryParams,
    CrashResponse,
    CustodyChainResponse,
    ReportResponse,
    Severity,
    ReportType
)

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ForensicEDR Cloud Backend",
    description="Production-ready cloud backend for crash data management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    logger.info("🚀 Starting ForensicEDR Cloud Backend...")
    await connect_to_mongodb()
    logger.info("✅ Application ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    logger.info("Shutting down...")
    await close_mongodb_connection()
    logger.info("✅ Shutdown complete")


# ============================================================================
# ENDPOINT 1: Health Check
# ============================================================================
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    
    Returns MongoDB connection status and basic system info
    """
    try:
        mongodb_status = await check_database_health()
        
        return HealthResponse(
            status="healthy" if mongodb_status['status'] == 'connected' else "degraded",
            database=mongodb_status['status'],
            timestamp=datetime.utcnow(),
            mongodb_status=mongodb_status
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            database="error",
            timestamp=datetime.utcnow(),
            mongodb_status={"error": str(e)}
        )


# ============================================================================
# ENDPOINT 2: Upload Evidence
# ============================================================================
@app.post("/api/v1/upload/evidence", response_model=UploadResponse, tags=["Evidence"])
async def upload_evidence(
    file: UploadFile = File(...),
    custody_log: Optional[str] = Form(None)
):
    """
    Upload encrypted crash evidence from edge device
    
    - Decrypts AES-256-GCM encrypted .bin file
    - Stores in MongoDB (crash_events + raw_telemetry)
    - Processes edge device custody log (if provided)
    - Creates cloud receipt custody log entry
    
    Args:
        file: Encrypted .bin file (multipart/form-data)
        custody_log: JSON string of edge device custody log (optional)
        
    Returns:
        UploadResponse with event_id and timestamp
    """
    try:
        # Read encrypted file
        encrypted_data = await file.read()
        logger.info(f"Received evidence file: {file.filename}, size: {len(encrypted_data)} bytes")
        
        # Decrypt
        event_data = decrypt_evidence(encrypted_data)
        event_id = event_data.get('event_id')
        
        if not event_id:
            raise ValueError("Missing event_id in decrypted data")
        
        # Get database
        db = await get_database()
        
        # Convert timestamp string to datetime if needed
        if isinstance(event_data.get('timestamp'), str):
            event_data['timestamp'] = datetime.fromisoformat(event_data['timestamp'].replace('Z', '+00:00'))
        
        # Convert location to GeoJSON format if needed
        if 'location' in event_data:
            loc = event_data['location']
            if 'latitude' in loc and 'longitude' in loc:
                # Convert to GeoJSON Point
                event_data['location'] = {
                    'type': 'Point',
                    'coordinates': [loc['longitude'], loc['latitude']],
                    'address': loc.get('address')
                }
        
        # Store crash event
        await db.crash_events.insert_one(event_data)
        logger.info(f"✅ Stored crash event: {event_id}")
        
        # Store raw telemetry if present
        if 'raw_data' in event_data and event_data['raw_data']:
            telemetry_doc = {
                'event_id': event_id,
                'timestamp': event_data['timestamp'],
                'telemetry_data': event_data['raw_data'],
                'created_at': datetime.utcnow()
            }
            await db.raw_telemetry.insert_one(telemetry_doc)
            logger.info(f"✅ Stored telemetry data for: {event_id}")
            
        # Process Edge Device Custody Log
        if custody_log:
            try:
                edge_log_data = json.loads(custody_log)
                
                # Ensure timestamp is datetime
                if isinstance(edge_log_data.get('timestamp'), str):
                    edge_log_data['timestamp'] = datetime.fromisoformat(edge_log_data['timestamp'].replace('Z', '+00:00'))
                
                # Insert into database
                # Note: We use try/except for duplicate key errors if retry happens
                try:
                    await db.evidence_custody_logs.insert_one(edge_log_data)
                    logger.info(f"✅ Stored edge custody log: {edge_log_data.get('entry_id')}")
                except Exception as e:
                    logger.warning(f"Could not store edge log (might exist): {e}")
                    
            except json.JSONDecodeError:
                logger.error("Failed to parse custody_log JSON string")
            except Exception as e:
                logger.error(f"Error processing edge custody log: {e}")
        
        # Create Cloud Receipt Custody Log
        # This will automatically link to the edge log we just inserted (if timestamps are correct)
        custody_manager = CustodyChainManager(db)
        await custody_manager.add_custody_entry(
            event_id=event_id,
            action="TRANSFER",
            actor="CLOUD_API",
            location="CLOUD_SERVER",
            details={
                'upload_info': {
                    'filename': file.filename,
                    'file_size': len(encrypted_data),
                    'content_type': file.content_type,
                    'edge_log_received': bool(custody_log)
                }
            }
        )
        logger.info(f"✅ Created cloud custody log for: {event_id}")
        
        return UploadResponse(
            status="success",
            event_id=event_id,
            timestamp=datetime.utcnow(),
            message="Evidence uploaded and stored successfully"
        )
        
    except ValueError as e:
        logger.error(f"Decryption/validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ============================================================================
# ENDPOINT 3: Query Crashes
# ============================================================================
@app.get("/api/v1/crashes", response_model=List[CrashResponse], tags=["Crashes"])
async def get_crashes(
    severity: Optional[Severity] = Query(None, description="Filter by severity"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    skip: int = Query(0, ge=0, description="Skip results for pagination")
):
    """
    Query crash events with filtering
    
    - Filter by severity, date range
    - Pagination support
    
    Returns list of crash events
    """
    try:
        db = await get_database()
        
        # Build query
        query = {}
        if severity:
            query['severity'] = severity.value
        
        if start_date or end_date:
            query['timestamp'] = {}
            if start_date:
                query['timestamp']['$gte'] = start_date
            if end_date:
                query['timestamp']['$lte'] = end_date
        
        # Execute query
        cursor = db.crash_events.find(query).skip(skip).limit(limit).sort('timestamp', -1)
        crashes = await cursor.to_list(length=limit)
        
        # Convert to response models
        results = []
        for crash in crashes:
            results.append(CrashResponse(
                event_id=crash['event_id'],
                timestamp=crash['timestamp'],
                crash_type=crash['crash_type'],
                severity=crash['severity'],
                location=crash['location'],
                calculated_values=crash['calculated_values'],
                metadata=crash['metadata']
            ))
        
        logger.info(f"Query returned {len(results)} crashes")
        return results
        
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINT 4: Get Specific Crash
# ============================================================================
@app.get("/api/v1/crashes/{event_id}", tags=["Crashes"])
async def get_crash_by_id(event_id: str):
    """
    Get complete crash data by event_id
    
    Includes telemetry and custody chain
    """
    try:
        db = await get_database()
        
        # Get crash event
        crash = await db.crash_events.find_one({'event_id': event_id})
        if not crash:
            raise HTTPException(status_code=404, detail=f"Crash event not found: {event_id}")
        
        # Get telemetry
        telemetry = await db.raw_telemetry.find_one({'event_id': event_id})
        
        # Get custody chain
        custody_manager = CustodyChainManager(db)
        custody_chain = await custody_manager.get_custody_chain(event_id)
        
        # Remove MongoDB _id fields
        crash.pop('_id', None)
        if telemetry:
            telemetry.pop('_id', None)
        for entry in custody_chain:
            entry.pop('_id', None)
        
        return {
            'crash_event': crash,
            'telemetry': telemetry,
            'custody_chain': custody_chain
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get crash {event_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINT 5: Geospatial Search
# ============================================================================
@app.get("/api/v1/crashes/nearby", tags=["Crashes"])
async def get_crashes_nearby(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius_km: float = Query(..., gt=0, le=100, description="Search radius in kilometers")
):
    """
    Find crashes near a location using geospatial queries
    
    Uses MongoDB 2dsphere index for efficient geospatial search
    """
    try:
        db = await get_database()
        
        # Convert km to meters
        radius_meters = radius_km * 1000
        
        # Geospatial query
        query = {
            'location': {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [longitude, latitude]
                    },
                    '$maxDistance': radius_meters
                }
            }
        }
        
        cursor = db.crash_events.find(query).limit(100)
        crashes = await cursor.to_list(length=100)
        
        # Remove _id fields
        for crash in crashes:
            crash.pop('_id', None)
        
        logger.info(f"Found {len(crashes)} crashes within {radius_km}km of ({latitude}, {longitude})")
        return crashes
        
    except Exception as e:
        logger.error(f"Geospatial query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINT 6: Generate Reports
# ============================================================================
@app.get("/api/v1/reports/generate", response_model=ReportResponse, tags=["Reports"])
async def generate_report(
    report_type: ReportType = Query(..., description="Type of report"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    format: str = Query("json", regex="^(json|html|png)$", description="Export format"),
    save_to_cache: bool = Query(True, description="Save report to cache for dashboard")
):
    """
    Generate analytical report with Plotly visualizations and optionally cache it
    
    Report types:
    - severity: Pie chart of crash severity distribution
    - timeline: Line chart of crashes over time
    - geographic: Map with crash locations
    - crash_type: Bar chart by crash type
    - impact: Scatter plot of impact force vs severity
    
    Formats: json, html, png
    
    Set save_to_cache=true to store in database for dashboard retrieval
    """
    try:
        db = await get_database()
        report_gen = ReportGenerator(db)
        
        result = await report_gen.generate_report(
            report_type=report_type.value,
            start_date=start_date,
            end_date=end_date,
            format=format,
            save_to_cache=save_to_cache
        )
        
        logger.info(f"Generated {report_type.value} report in {format} format (cached: {result.get('cached', False)})")
        return ReportResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NEW ENDPOINT: Get Cached Report by ID
# ============================================================================
@app.get("/api/v1/reports/{report_id}", tags=["Reports"])
async def get_cached_report(report_id: str):
    """
    Retrieve a previously generated report from cache
    
    Use this endpoint in your dashboard to quickly load cached reports
    without regenerating them.
    """
    try:
        db = await get_database()
        report_gen = ReportGenerator(db)
        
        report = await report_gen.get_cached_report(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail=f"Cached report not found: {report_id}")
        
        logger.info(f"Retrieved cached report: {report_id}")
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve cached report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NEW ENDPOINT: Get All Recent Cached Reports
# ============================================================================
@app.get("/api/v1/reports/cached/recent", tags=["Reports"])
async def get_recent_cached_reports(limit: int = Query(10, ge=1, le=50, description="Max reports to return")):
    """
    Get recently generated cached reports for dashboard
    
    Returns the most recent cached reports sorted by generation time.
    Use this to show report history in your dashboard.
    """
    try:
        db = await get_database()
        report_gen = ReportGenerator(db)
        
        reports = await report_gen.get_latest_reports(limit=limit)
        
        logger.info(f"Retrieved {len(reports)} recent cached reports")
        return {
            "total": len(reports),
            "reports": reports
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve recent reports: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINT 7: Get Custody Chain
# ============================================================================
@app.get("/api/v1/custody/{event_id}", response_model=CustodyChainResponse, tags=["Custody Chain"])
async def get_custody_chain(event_id: str):
    """
    Get complete custody chain for an event with verification
    
    Returns chain of custody logs with integrity verification status
    """
    try:
        db = await get_database()
        custody_manager = CustodyChainManager(db)
        
        # Get custody chain
        chain = await custody_manager.get_custody_chain(event_id)
        
        if not chain:
            raise HTTPException(status_code=404, detail=f"No custody logs found for event: {event_id}")
        
        # Verify chain integrity
        verification = await custody_manager.verify_chain(event_id)
        
        # Remove _id fields
        for entry in chain:
            entry.pop('_id', None)
        
        return CustodyChainResponse(
            event_id=event_id,
            chain=chain,
            chain_valid=verification['valid'],
            chain_length=verification['chain_length'],
            verification_details=verification
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get custody chain for {event_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "ForensicEDR Cloud Backend",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "upload": "/api/v1/upload/evidence",
            "crashes": "/api/v1/crashes",
            "nearby": "/api/v1/crashes/nearby",
            "reports_generate": "/api/v1/reports/generate",
            "reports_cached": "/api/v1/reports/{report_id}",
            "reports_recent": "/api/v1/reports/cached/recent",
            "custody": "/api/v1/custody/{event_id}"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
