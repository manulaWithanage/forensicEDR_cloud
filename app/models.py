"""Pydantic models for request/response validation"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class CrashType(str, Enum):
    FRONTAL_IMPACT = "frontal_impact_collision"
    SIDE_IMPACT = "side_impact_collision"
    REAR_END = "rear_end_collision"
    ROLLOVER = "rollover_event"


class Severity(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"


class CustodyAction(str, Enum):
    EVIDENCE_COLLECTION = "EVIDENCE_COLLECTION"
    TRANSFER = "TRANSFER"
    ACCESS = "ACCESS"
    VERIFICATION = "VERIFICATION"
    MODIFICATION = "MODIFICATION"
    EXPORT = "EXPORT"
    DELETION = "DELETION"


class ReportType(str, Enum):
    SEVERITY = "severity"
    TIMELINE = "timeline"
    GEOGRAPHIC = "geographic"
    CRASH_TYPE = "crash_type"
    IMPACT = "impact"


# GeoJSON Models
class GeoJSONPoint(BaseModel):
    type: str = "Point"
    coordinates: List[float] = Field(..., min_items=2, max_items=2)  # [longitude, latitude]


class Location(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]
    address: Optional[str] = None


# Crash Event Models
class CalculatedValues(BaseModel):
    speed_now: Optional[float] = None
    speed_previous: Optional[float] = None
    deceleration: Optional[float] = None
    total_acceleration: Optional[float] = None
    angular_acceleration: Optional[float] = None
    hard_brake_event: Optional[str] = None
    airbag_status: Optional[str] = None
    power_status: Optional[str] = None
    tilt: Optional[float] = None
    impact_force_g: Optional[float] = None


class Metadata(BaseModel):
    csv_file: Optional[str] = None
    buffer_seconds: int = 60
    window_size: int = 10
    detection_algorithm: str = "rule_based_v1"
    device_id: str
    firmware_version: str = "1.0.0"


class ChainOfCustody(BaseModel):
    collection_timestamp: datetime
    collected_by: str
    location: str
    hash_chain: str
    encryption: str = "AES-256-GCM"
    tamper_proof: bool = True


class TelemetryRecord(BaseModel):
    timestamp: str
    speed: float
    rpm: int
    throttle_pos: int
    engine_load: Optional[float] = None
    coolant_temp: Optional[float] = None
    fuel_level: Optional[float] = None
    latitude: float
    longitude: float
    accel_x: float
    accel_y: float
    accel_z: float
    airbag_status: str
    power_status: str
    tilt: float
    total_acceleration: float
    angular_acceleration: float
    hard_brake_event: int
    event: Optional[str] = None


class CrashEvent(BaseModel):
    event_id: str
    timestamp: datetime
    crash_event: str
    crash_type: CrashType
    severity: Severity
    location: Location
    raw_data: Optional[List[TelemetryRecord]] = None
    calculated_values: CalculatedValues
    metadata: Metadata
    chain_of_custody: Optional[ChainOfCustody] = None


# Custody Chain Models
class ActorDetails(BaseModel):
    system_id: Optional[str] = None
    firmware_version: Optional[str] = None
    ip_address: Optional[str] = None
    user_id: Optional[str] = None


class CustodyLog(BaseModel):
    entry_id: str
    timestamp: datetime
    event_id: str
    action: CustodyAction
    actor: str
    actor_type: str = "AUTOMATED_SYSTEM"
    actor_details: Optional[ActorDetails] = None
    location: str
    details: Dict[str, Any]
    previous_hash: str
    entry_hash: str
    hash_algorithm: str = "SHA-256"
    verified: bool = True
    created_at: Optional[datetime] = None


# Request/Response Models
class UploadResponse(BaseModel):
    status: str = "success"
    event_id: str
    timestamp: datetime
    message: str = "Evidence uploaded and stored successfully"


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime
    mongodb_status: Optional[Dict[str, Any]] = None


class CrashQueryParams(BaseModel):
    severity: Optional[Severity] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    skip: int = Field(default=0, ge=0)


class NearbyQueryParams(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(..., gt=0, le=100)


class ReportQueryParams(BaseModel):
    report_type: ReportType
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    format: str = Field(default="json", pattern="^(json|html|png)$")


class CrashResponse(BaseModel):
    event_id: str
    timestamp: datetime
    crash_type: CrashType
    severity: Severity
    location: Location
    calculated_values: CalculatedValues
    metadata: Metadata


class CustodyChainResponse(BaseModel):
    event_id: str
    chain: List[CustodyLog]
    chain_valid: bool
    chain_length: int
    verification_details: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    report_type: str
    generated_at: datetime
    data: Dict[str, Any]
    format: str
