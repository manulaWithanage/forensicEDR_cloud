# ForensicEDR Cloud Backend - Scripts

This directory contains utility scripts for database management and testing.

## Database Management

### `setup_db.py`
Initialize MongoDB collections, indexes, and insert sample data.

```bash
python scripts/setup_db.py
```

**What it does:**
- Creates all required collections with validation schemas
- Sets up indexes (including 2dsphere for geospatial queries)
- Inserts sample crash data for testing

### `clean_db.py`
Remove all documents from all collections while preserving schema.

```bash
python scripts/clean_db.py
```

**Use case:** Clean slate before re-populating with fresh data.

### `populate_db.py`
Generate and upload randomized crash events for testing/demo.

```bash
python scripts/populate_db.py
```

**What it generates:**
- 15 crash events with varied severity and types
- Locations around Colombo, Sri Lanka
- Full custody chain (Edge → Cloud)
- Encrypted evidence files

## Testing

### `test_upload_v2.py`
Comprehensive test for the upload endpoint with custody log support.

```bash
python scripts/test_upload_v2.py
```

**What it tests:**
- AES-256-GCM encryption
- Custody log creation and verification
- Chain linking (Edge → Cloud)
- Database storage

### `test_db_connection_v2.py`
Verify MongoDB connection with current credentials.

```bash
python scripts/test_db_connection_v2.py
```

**Use case:** Quick connectivity check before running other scripts.

### `sample_upload.py`
Legacy upload test (kept for reference).

```bash
python scripts/sample_upload.py
```

## Script Dependencies

All scripts require:
- `.env` file configured with `MONGODB_URI` and `AES_ENCRYPTION_KEY`
- Python packages from `requirements.txt`
- Running MongoDB instance (local or Atlas)

## Recommended Workflow

1. **Initial Setup:**
   ```bash
   python scripts/setup_db.py
   ```

2. **Test Upload:**
   ```bash
   python scripts/test_upload_v2.py
   ```

3. **Populate Demo Data:**
   ```bash
   python scripts/populate_db.py
   ```

4. **Clean and Reset:**
   ```bash
   python scripts/clean_db.py
   python scripts/populate_db.py
   ```
