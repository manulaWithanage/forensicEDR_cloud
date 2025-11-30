# ForensicEDR Cloud Backend

Production-ready cloud backend system for ForensicEDR that receives crash data from edge devices, stores in MongoDB, and generates analytical reports.

## 🏗️ Architecture

```
Edge Device → FastAPI Backend → MongoDB
                    ↓
            Plotly Reports
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- MongoDB URI (Atlas or local instance)
- AES-256 encryption key

### Installation

1. **Clone and navigate to project:**
```bash
cd ForensicEDR_Cloud_Backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your MongoDB URI and encryption key
```

5. **Initialize database:**
```bash
python scripts/setup_db.py
```

6. **Run development server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API available at: http://localhost:8000

Interactive docs at: http://localhost:8000/docs

---

## 🐳 Docker Deployment

### Production deployment with Docker Compose:

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

---

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with MongoDB status |
| `/api/v1/upload/evidence` | POST | Upload encrypted crash evidence |
| `/api/v1/crashes` | GET | Query crash events with filters |
| `/api/v1/crashes/{event_id}` | GET | Get specific crash details |
| `/api/v1/crashes/nearby` | GET | Geospatial search for crashes |
| `/api/v1/reports/generate` | GET | Generate analytical reports |
| `/api/v1/custody/{event_id}` | GET | Get custody chain with verification |

See [API_DOCS.md](API_DOCS.md) for detailed documentation.

---

## 🧪 Testing

### Run test suite:
```bash
pytest tests/ -v
```

### Test evidence upload:
```bash
python scripts/sample_upload.py
```

### Test specific endpoint:
```bash
curl http://localhost:8000/health
curl "http://localhost:8000/api/v1/crashes?severity=severe&limit=10"
```

---

## 🗄️ MongoDB Collections

1. **crash_events** - Crash metadata with GeoJSON location
2. **raw_telemetry** - 60-second sensor buffer data
3. **evidence_custody_logs** - Blockchain-style custody chain

### Required Indexes:
- `crash_events.location` (2dsphere) for geospatial queries
- `crash_events.event_id` (unique)
- `evidence_custody_logs.entry_hash` (unique)

---

## 🔐 Security Features

- **AES-256-GCM** encryption for evidence files
- **SHA-256** blockchain-style custody chain
- **TLS 1.3** recommended for production
- **ISO 27037** and **NIST SP 800-86** compliant

---

## 📈 Report Types

1. **Severity Distribution** - Pie chart of crash severity levels
2. **Crashes Over Time** - Timeline analysis
3. **Geographic Distribution** - Map with crash locations
4. **Crash Type Breakdown** - Bar chart by crash type
5. **Impact Force Analysis** - Scatter plot correlation

---

## 🛠️ Development

### Project Structure:
```
ForensicEDR_Cloud_Backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── database.py          # MongoDB connection
│   ├── models.py            # Pydantic models
│   ├── encryption.py        # AES-256-GCM utilities
│   ├── custody_chain.py     # Hash chain manager
│   ├── report_generator.py  # Plotly visualizations
│   └── config.py            # Configuration
├── scripts/
│   ├── setup_db.py          # Database initialization
│   └── sample_upload.py     # Test data generator
├── tests/
│   └── test_api.py          # API tests
├── requirements.txt
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

---

## 📝 Environment Variables

Required in `.env`:
```
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/forensic_edr
AES_ENCRYPTION_KEY=<64-character hex string>
API_SECRET_KEY=<your-secret-key>
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
CORS_ORIGINS=*
```

Generate encryption key:
```python
import secrets
print(secrets.token_hex(32))  # 32 bytes = 64 hex chars
```

---

## 🚨 Troubleshooting

**MongoDB connection fails:**
- Check MONGODB_URI in .env
- Verify network connectivity
- Ensure IP whitelist in MongoDB Atlas

**Decryption errors:**
- Verify AES_ENCRYPTION_KEY matches edge device key
- Check .bin file format (12-byte nonce + 16-byte tag + ciphertext)

**Geospatial queries fail:**
- Ensure 2dsphere index exists: `python scripts/setup_db.py`
- Verify GeoJSON format: `{type: "Point", coordinates: [lng, lat]}`

---

## 📚 Standards Compliance

- **ISO/IEC 27037:2012** - Digital evidence identification and preservation
- **NIST SP 800-86** - Guide to Integrating Forensic Techniques
- **FIPS 180-4** - SHA-256 hash function
- **NIST SP 800-38D** - AES-GCM encryption

---

## 📄 License

ForensicEDR Cloud Backend © 2024

---

## 🤝 Support

For issues and questions, refer to [API_DOCS.md](API_DOCS.md) for detailed endpoint documentation.
