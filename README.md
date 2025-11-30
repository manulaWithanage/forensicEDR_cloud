# ForensicEDR Cloud Backend

A production-ready cloud backend for vehicle crash forensic evidence management, featuring secure data handling, blockchain-inspired custody chains, and real-time analytics.

## 🚀 Features

- **Secure Evidence Upload**: AES-256-GCM encryption for crash data
- **Blockchain-Inspired Custody Chain**: SHA-256 hash chain for tamper detection
- **Geospatial Queries**: MongoDB 2dsphere indexing for location-based searches
- **Real-time Analytics**: Plotly-powered report generation with caching
- **RESTful API**: FastAPI with automatic OpenAPI documentation
- **Cloud-Ready**: Configured for Render.com deployment

## 📋 Prerequisites

- Python 3.11+
- MongoDB Atlas account (or local MongoDB)
- Git

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/manulaWithanage/forensicEDR_cloud.git
cd ForensicEDR_Cloud_Backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy `.env.example` to `.env` and update:

```env
MONGODB_URI=your_mongodb_connection_string
AES_ENCRYPTION_KEY=your_64_char_hex_key
```

Generate encryption key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Initialize Database

```bash
python scripts/setup_db.py
```

## 🚦 Running the Server

### Development

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Access the API documentation at: `http://localhost:8000/docs`

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health check |
| POST | `/api/v1/upload/evidence` | Upload encrypted crash evidence |
| GET | `/api/v1/crashes` | List crashes (with filters) |
| GET | `/api/v1/crashes/{event_id}` | Get crash details |
| GET | `/api/v1/crashes/nearby` | Geospatial search |
| GET | `/api/v1/custody/{event_id}` | Verify custody chain |
| GET | `/api/v1/reports/generate` | Generate analytics report |
| GET | `/api/v1/reports/cached/recent` | Get recent cached reports |
| GET | `/api/v1/reports/{report_id}` | Get cached report by ID |

## 🧪 Testing

### Run Test Suite

```bash
pytest tests/ -v
```

### Test Upload Endpoint

```bash
python scripts/test_upload_v2.py
```

### Populate Sample Data

```bash
python scripts/populate_db.py
```

### Clean Database

```bash
python scripts/clean_db.py
```

## 📦 Project Structure

```
ForensicEDR_Cloud_Backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── database.py          # MongoDB connection
│   ├── models.py            # Pydantic models
│   ├── encryption.py        # AES-256-GCM encryption
│   ├── custody_chain.py     # SHA-256 hash chain
│   └── report_generator.py # Plotly analytics
├── scripts/
│   ├── setup_db.py          # Database initialization
│   ├── populate_db.py       # Sample data generator
│   ├── clean_db.py          # Database cleanup
│   └── test_upload_v2.py    # Upload verification
├── tests/
│   └── test_api.py          # API tests
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
└── render.yaml             # Render deployment config
```

## 🔐 Security Features

### Encryption
- **Algorithm**: AES-256-GCM
- **Key Management**: Environment variable-based
- **Data Format**: Nonce (12 bytes) + Tag (16 bytes) + Ciphertext

### Custody Chain
- **Hash Algorithm**: SHA-256
- **Chain Structure**: Each entry links to previous via hash
- **Tamper Detection**: Automatic verification on retrieval
- **Edge-to-Cloud**: Preserves custody from device to cloud

## 🌐 Deployment

### Render.com (Recommended)

1. Push code to GitHub
2. Create new Web Service on Render
3. Connect repository
4. Set environment variables
5. Deploy

See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for detailed instructions.

### Docker

```bash
docker-compose up -d
```

## 📊 Data Models

### Crash Event
```json
{
  "event_id": "evt_20251130_001",
  "timestamp": "2025-11-30T10:30:00Z",
  "crash_type": "frontal_impact_collision",
  "severity": "severe",
  "location": {
    "type": "Point",
    "coordinates": [79.8612, 6.9271],
    "address": "Colombo, Sri Lanka"
  },
  "calculated_values": {
    "impact_force_g": 4.5,
    "deceleration": -65.5,
    "speed_previous": 80.0
  }
}
```

### Custody Log
```json
{
  "entry_id": "log_001",
  "event_id": "evt_20251130_001",
  "action": "EVIDENCE_COLLECTION",
  "actor": "EDGE_DEVICE_V2",
  "timestamp": "2025-11-30T10:30:00Z",
  "previous_hash": "0000...0000",
  "entry_hash": "a1b2c3d4..."
}
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License.

## 👥 Authors

- **Manula Withanage** - [GitHub](https://github.com/manulaWithanage)

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- MongoDB for flexible data storage
- Plotly for powerful visualizations
- Render.com for seamless deployment
