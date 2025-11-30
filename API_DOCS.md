# ForensicEDR Cloud Backend API Documentation

Complete API reference for the ForensicEDR Cloud Backend system.

**Base URL:** `http://localhost:8000` (development)  
**API Version:** v1  
**Interactive Docs:** `/docs` (Swagger UI) | `/redoc` (ReDoc)

---

## Authentication

Currently no authentication required. For production, implement API keys or OAuth2.

---

## Endpoints Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with MongoDB status |
| `/api/v1/upload/evidence` | POST | Upload encrypted crash evidence |
| `/api/v1/crashes` | GET | Query crash events with filters |
| `/api/v1/crashes/{event_id}` | GET | Get specific crash details |
| `/api/v1/crashes/nearby` | GET | Geospatial search for crashes |
| `/api/v1/reports/generate` | GET | Generate analytical reports |
| `/api/v1/custody/{event_id}` | GET | Get custody chain with verification |

---

## 1. Health Check

**GET** `/health`

Check system health and MongoDB connection status.

### Response

```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-12-01T00:15:32.123456Z",
  "mongodb_status": {
    "status": "connected",
    "database": "forensic_edr",
    "version": "7.0.0",
    "uptime": 3600
  }
}
```

### cURL Example

```bash
curl http://localhost:8000/health
```

---

## 2. Upload Evidence

**POST** `/api/v1/upload/evidence`

Upload encrypted crash evidence from edge device.

### Request

- **Content-Type:** `multipart/form-data`
- **Body:** Binary .bin file (AES-256-GCM encrypted)

### File Format

```
Bytes 0-11:   Nonce (12 bytes)
Bytes 12-27:  Authentication tag (16 bytes)
Bytes 28+:    Encrypted JSON ciphertext
```

### Response

```json
{
  "status": "success",
  "event_id": "event_2024-12-01_00-15-32",
  "timestamp": "2024-12-01T00:15:33.000000Z",
  "message": "Evidence uploaded and stored successfully"
}
```

### cURL Example

```bash
curl -X POST http://localhost:8000/api/v1/upload/evidence \
  -F "file=@crash_evidence.bin"
```

### Error Responses

- **400:** Decryption failed or invalid data
- **500:** Server error during storage

---

## 3. Query Crashes

**GET** `/api/v1/crashes`

Query crash events with optional filters and pagination.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `severity` | string | No | Filter by severity (minor/moderate/severe) |
| `start_date` | datetime (ISO) | No | Start date for time range |
| `end_date` | datetime (ISO) | No | End date for time range |
| `limit` | integer | No | Max results (default: 100, max: 1000) |
| `skip` | integer | No | Results to skip for pagination (default: 0) |

### Response

```json
[
  {
    "event_id": "event_2024-11-30_18-15-32",
    "timestamp": "2024-11-30T18:15:32.456789Z",
    "crash_type": "frontal_impact_collision",
    "severity": "severe",
    "location": {
      "type": "Point",
      "coordinates": [79.8625, 6.9284],
      "address": "Colombo, Sri Lanka"
    },
    "calculated_values": {
      "speed_now": 0.0,
      "impact_force_g": 1.34,
      ...
    },
    "metadata": {
      "device_id": "EDR_DEVICE_001",
      ...
    }
  }
]
```

### cURL Examples

```bash
# Get all crashes (paginated)
curl "http://localhost:8000/api/v1/crashes?limit=10"

# Filter by severity
curl "http://localhost:8000/api/v1/crashes?severity=severe"

# Filter by date range
curl "http://localhost:8000/api/v1/crashes?start_date=2024-11-01T00:00:00Z&end_date=2024-12-01T23:59:59Z"

# Pagination
curl "http://localhost:8000/api/v1/crashes?limit=50&skip=100"
```

---

## 4. Get Crash by ID

**GET** `/api/v1/crashes/{event_id}`

Retrieve complete crash data including telemetry and custody chain.

### Path Parameters

- `event_id` (string, required): Event identifier

### Response

```json
{
  "crash_event": {
    "event_id": "event_2024-11-30_18-15-32",
    "timestamp": "2024-11-30T18:15:32.456789Z",
    "crash_type": "frontal_impact_collision",
    "severity": "severe",
    "location": {...},
    "raw_data": [...],
    "calculated_values": {...},
    "metadata": {...}
  },
  "telemetry": {
    "event_id": "event_2024-11-30_18-15-32",
    "telemetry_data": [...]
  },
  "custody_chain": [
    {
      "entry_id": "custody_001",
      "action": "EVIDENCE_COLLECTION",
      "timestamp": "2024-11-30T18:15:32.500Z",
      ...
    }
  ]
}
```

### cURL Example

```bash
curl http://localhost:8000/api/v1/crashes/event_2024-11-30_18-15-32
```

### Error Responses

- **404:** Event not found

---

## 5. Geospatial Search

**GET** `/api/v1/crashes/nearby`

Find crashes near a location using MongoDB 2dsphere index.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `latitude` | float | Yes | Latitude (-90 to 90) |
| `longitude` | float | Yes | Longitude (-180 to 180) |
| `radius_km` | float | Yes | Search radius in kilometers (max: 100) |

### Response

Returns array of crash events within the specified radius, sorted by distance (nearest first).

```json
[
  {
    "event_id": "event_2024-11-30_18-15-32",
    "location": {
      "type": "Point",
      "coordinates": [79.8625, 6.9284]
    },
    ...
  }
]
```

### cURL Example

```bash
# Find crashes within 5km of Colombo Fort
curl "http://localhost:8000/api/v1/crashes/nearby?latitude=6.9271&longitude=79.8612&radius_km=5"
```

---

## 6. Generate Reports

**GET** `/api/v1/reports/generate`

Generate analytical reports with Plotly visualizations.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `report_type` | string | Yes | Report type (see below) |
| `start_date` | datetime (ISO) | No | Start date filter |
| `end_date` | datetime (ISO) | No | End date filter |
| `format` | string | No | Export format: json/html/png (default: json) |

### Report Types

1. **severity** - Pie chart of crash severity distribution
2. **timeline** - Line chart of crashes over time
3. **geographic** - Map with crash locations (color-coded by severity)
4. **crash_type** - Bar chart of crash types
5. **impact** - Scatter plot of impact force vs total acceleration

### Response (format=json)

```json
{
  "report_type": "severity",
  "generated_at": "2024-12-01T00:15:32.000000Z",
  "format": "json",
  "data": "{...plotly figure JSON...}"
}
```

### Response (format=png)

```json
{
  "report_type": "geographic",
  "generated_at": "2024-12-01T00:15:32.000000Z",
  "format": "png",
  "data": "data:image/png;base64,iVBORw0KG..."
}
```

### cURL Examples

```bash
# Generate severity distribution pie chart (JSON)
curl "http://localhost:8000/api/v1/reports/generate?report_type=severity&format=json"

# Generate geographic map (HTML)
curl "http://localhost:8000/api/v1/reports/generate?report_type=geographic&format=html" > report.html

# Generate timeline with date filter (PNG)
curl "http://localhost:8000/api/v1/reports/generate?report_type=timeline&start_date=2024-11-01T00:00:00Z&format=png"
```

---

## 7. Get Custody Chain

**GET** `/api/v1/custody/{event_id}`

Retrieve complete custody chain with cryptographic verification.

### Path Parameters

- `event_id` (string, required): Event identifier

### Response

```json
{
  "event_id": "event_2024-11-30_18-15-32",
  "chain_valid": true,
  "chain_length": 3,
  "verification_details": {
    "valid": true,
    "chain_length": 3,
    "message": "Chain integrity verified successfully"
  },
  "chain": [
    {
      "entry_id": "custody_000001",
      "timestamp": "2024-11-30T18:15:32.500Z",
      "event_id": "event_2024-11-30_18-15-32",
      "action": "EVIDENCE_COLLECTION",
      "actor": "CRASH_DETECTION_SYSTEM",
      "location": "EDGE_DEVICE",
      "previous_hash": "GENESIS",
      "entry_hash": "a3f5e9c8d2b1a4f7e6c9d8b3a2f5e9c8d2b1a4f7",
      "hash_algorithm": "SHA-256",
      "verified": true
    },
    {
      "entry_id": "custody_000002",
      "timestamp": "2024-11-30T18:15:35.200Z",
      "action": "TRANSFER",
      "actor": "CLOUD_API",
      "location": "CLOUD_SERVER",
      "previous_hash": "a3f5e9c8d2b1a4f7e6c9d8b3a2f5e9c8d2b1a4f7",
      "entry_hash": "b7d4e2a1c5f8e9d3b6a7c4f2e8d1a5b9c6f3e7d2",
      ...
    }
  ]
}
```

### cURL Example

```bash
curl http://localhost:8000/api/v1/custody/event_2024-11-30_18-15-32
```

### Verification Details

- **chain_valid: true** - Chain integrity verified, no tampering detected
- **chain_valid: false** - Chain broken, tampering detected (see verification_details for error)

### Error Responses

- **404:** No custody logs found for event

---

## Data Models

### Location (GeoJSON)

```json
{
  "type": "Point",
  "coordinates": [longitude, latitude],  // Note: longitude first!
  "address": "Optional human-readable address"
}
```

### Calculated Values

```json
{
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
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad request (validation error, decryption failure) |
| 404 | Resource not found |
| 500 | Internal server error |

---

## Rate Limiting

Currently not implemented. For production, consider implementing rate limiting per IP or API key.

---

## Security Considerations

1. **Encryption:** All evidence files must be encrypted with AES-256-GCM
2. **Custody Chain:** SHA-256 hash chain ensures tamper detection
3. **TLS Required:** Use HTTPS in production
4. **MongoDB Security:** Use MongoDB authentication and IP whitelisting
5. **Environment Variables:** Never commit .env file with real credentials

---

## Testing

### Using cURL

```bash
# 1. Check health
curl http://localhost:8000/health

# 2. Upload evidence
python scripts/sample_upload.py

# 3. Query crashes
curl "http://localhost:8000/api/v1/crashes?severity=severe"

# 4. Generate report
curl "http://localhost:8000/api/v1/reports/generate?report_type=severity" > report.json

# 5. Verify custody chain
curl http://localhost:8000/api/v1/custody/event_2024-11-30_18-15-32
```

### Using Python

```python
import httpx
import asyncio

async def test_api():
    async with httpx.AsyncClient() as client:
        # Health check
        response = await client.get("http://localhost:8000/health")
        print(response.json())
        
        # Query crashes
        response = await client.get(
            "http://localhost:8000/api/v1/crashes",
            params={"severity": "severe", "limit": 10}
        )
        crashes = response.json()
        print(f"Found {len(crashes)} severe crashes")

asyncio.run(test_api())
```

---

## Standards Compliance

- **ISO/IEC 27037:2012** - Digital evidence identification and preservation
- **NIST SP 800-86** - Forensic techniques integration
- **FIPS 180-4** - SHA-256 hash function
- **NIST SP 800-38D** - AES-GCM encryption

---

## Support

For issues, refer to:
- **Interactive Docs:** http://localhost:8000/docs
- **README:** Project root README.md
- **Source Code:** Review individual modules in `app/` directory
