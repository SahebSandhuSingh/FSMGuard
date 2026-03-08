# FSMGuard Backend API

Complete REST API for the FSMGuard automated FSM security analysis pipeline.

## Features

- ✅ **File Upload**: Upload Verilog/SystemVerilog designs
- ✅ **Async Analysis**: Background pipeline execution with progress tracking
- ✅ **Real-time Status**: Check job progress and status
- ✅ **Results API**: Retrieve complete analysis results
- ✅ **File Downloads**: Download patched designs and security reports
- ✅ **Job Management**: List, track, and clean up analysis jobs

## Architecture

```
FSMGuard Backend
├── api.py              # FastAPI REST endpoints
├── pipeline_runner.py  # Pipeline execution engine
└── requirements.txt    # Backend dependencies
```

## Installation

### 1. Install Dependencies

```bash
# Core FSMGuard dependencies (from root)
pip install -r requirements.txt

# Backend-specific dependencies
pip install -r backend/requirements.txt
```

### 2. Verify Installation

```bash
# Test pipeline runner
python3 backend/pipeline_runner.py

# Should see test pipeline execution
```

## Running the Server

### Development Mode

```bash
# Start the API server
python3 backend/api.py

# Server runs on http://localhost:8000
# API docs available at http://localhost:8000/docs
```

### Production Mode

```bash
# Using uvicorn directly
uvicorn backend.api:app --host 0.0.0.0 --port 8000 --workers 4

# Or with gunicorn
gunicorn backend.api:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## API Endpoints

### Health Check

```http
GET /
GET /api/health
```

**Response:**
```json
{
  "service": "FSMGuard API",
  "status": "running",
  "version": "1.0.0"
}
```

### Upload File

```http
POST /api/upload
Content-Type: multipart/form-data

file: <verilog_file>
```

**Response:**
```json
{
  "job_id": "job-abc123def456",
  "filename": "design.v",
  "size": 5432,
  "status": "uploaded",
  "message": "File uploaded. Use /api/analyze/{job_id} to start analysis."
}
```

### Start Analysis

```http
POST /api/analyze/{job_id}
```

**Response:**
```json
{
  "job_id": "job-abc123def456",
  "status": "pending",
  "message": "Analysis started. Check /api/status/{job_id} for progress."
}
```

### Check Status

```http
GET /api/status/{job_id}
```

**Response:**
```json
{
  "job_id": "job-abc123def456",
  "status": "running",
  "progress": 45,
  "message": "Stage 5: Subgraph isolation...",
  "created_at": 1709856123.456,
  "updated_at": 1709856145.789
}
```

**Status Values:**
- `uploaded` - File uploaded, not started
- `pending` - Analysis queued
- `running` - Pipeline executing
- `completed` - Analysis complete
- `failed` - Error occurred

### Get Results

```http
GET /api/results/{job_id}
```

**Response:**
```json
{
  "job_id": "job-abc123def456",
  "status": "completed",
  "filename": "design.v",
  "vulnerabilities_found": 6,
  "vulnerabilities_fixed": 6,
  "design_safe": true,
  "stages": {
    "stage1": { "states": 6, "transitions": 11 },
    "stage3_4": { "weak_states": 6 },
    "stage5_10": { "patches_applied": 6 }
  },
  "files": {
    "patched": "/workspace/job-abc123/output/patched_fsm.v",
    "report": "/workspace/job-abc123/output/fsm_report.json"
  }
}
```

### Download Patched File

```http
GET /api/download/patched/{job_id}
```

**Response:** Verilog file download

### Download Report

```http
GET /api/download/report/{job_id}?format=json
GET /api/download/report/{job_id}?format=txt
```

**Response:** Report file download (JSON or text)

### Get Logs

```http
GET /api/logs/{job_id}
```

**Response:**
```json
{
  "job_id": "job-abc123def456",
  "stdout": "Pipeline execution logs...",
  "stderr": ""
}
```

### List Jobs

```http
GET /api/jobs
GET /api/jobs?status=running
GET /api/jobs?status=completed
```

**Response:**
```json
{
  "total": 5,
  "jobs": [
    {
      "job_id": "job-abc123",
      "status": "completed",
      "progress": 100,
      "created_at": 1709856123.456
    }
  ]
}
```

### Delete Job

```http
DELETE /api/job/{job_id}
```

**Response:**
```json
{
  "message": "Job job-abc123def456 deleted successfully"
}
```

## Usage Examples

### Python Client

```python
import requests

# 1. Upload file
with open("design.v", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/upload",
        files={"file": f}
    )
    job_id = response.json()["job_id"]

# 2. Start analysis
requests.post(f"http://localhost:8000/api/analyze/{job_id}")

# 3. Poll for status
import time
while True:
    status = requests.get(f"http://localhost:8000/api/status/{job_id}").json()
    print(f"Progress: {status['progress']}%")
    if status["status"] == "completed":
        break
    time.sleep(2)

# 4. Get results
results = requests.get(f"http://localhost:8000/api/results/{job_id}").json()
print(f"Vulnerabilities: {results['vulnerabilities_found']}")
print(f"Design Safe: {results['design_safe']}")

# 5. Download patched file
patched = requests.get(f"http://localhost:8000/api/download/patched/{job_id}")
with open("patched_design.v", "wb") as f:
    f.write(patched.content)
```

### cURL Examples

```bash
# Upload file
curl -X POST http://localhost:8000/api/upload \
  -F "file=@design.v"

# Start analysis
curl -X POST http://localhost:8000/api/analyze/job-abc123

# Check status
curl http://localhost:8000/api/status/job-abc123

# Get results
curl http://localhost:8000/api/results/job-abc123

# Download patched file
curl -O http://localhost:8000/api/download/patched/job-abc123

# Download report
curl -O http://localhost:8000/api/download/report/job-abc123?format=json
```

### JavaScript/TypeScript (Frontend)

```typescript
// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const uploadResponse = await fetch('http://localhost:8000/api/upload', {
  method: 'POST',
  body: formData
});
const { job_id } = await uploadResponse.json();

// Start analysis
await fetch(`http://localhost:8000/api/analyze/${job_id}`, {
  method: 'POST'
});

// Poll for status
const pollStatus = async () => {
  const response = await fetch(`http://localhost:8000/api/status/${job_id}`);
  const status = await response.json();
  
  if (status.status === 'completed') {
    // Get results
    const results = await fetch(`http://localhost:8000/api/results/${job_id}`);
    console.log(await results.json());
  } else if (status.status === 'running') {
    setTimeout(pollStatus, 2000); // Poll every 2 seconds
  }
};

pollStatus();
```

## Configuration

### Environment Variables

Create `.env` file in backend directory:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4

# File Upload
MAX_FILE_SIZE_MB=10
UPLOAD_DIR=uploads

# Workspace
WORKSPACE_DIR=workspace

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### File Limits

- **Max File Size**: 10 MB (configurable)
- **Allowed Extensions**: `.v`, `.sv`, `.vh`, `.svh`
- **Max Concurrent Jobs**: 4 workers

## Error Handling

### Common Error Codes

- `400` - Invalid request (wrong file type, file too large)
- `404` - Job not found
- `500` - Server error (pipeline failure)

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Testing

### Unit Tests

```bash
# Run backend tests
pytest backend/tests/

# With coverage
pytest --cov=backend backend/tests/
```

### Integration Tests

```bash
# Test complete workflow
python3 backend/test_api.py
```

## Monitoring

### Logs

```bash
# View live logs
tail -f logs/api.log

# Search for errors
grep ERROR logs/api.log
```

### Metrics

Available at `/api/health`:

- Active jobs count
- Total jobs processed
- Workspace usage

## Deployment

### Docker

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt
RUN pip install -r backend/requirements.txt

EXPOSE 8000

CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t fsmguard-api .
docker run -p 8000:8000 fsmguard-api
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./workspace:/app/workspace
      - ./uploads:/app/uploads
    environment:
      - WORKERS=4
      - MAX_FILE_SIZE_MB=10
```

## Troubleshooting

### Issue: Pipeline fails with import errors

**Solution:**
```bash
# Ensure all dependencies installed
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

### Issue: Jobs stay in "pending" status

**Solution:**
- Check backend logs for errors
- Verify worker threads are running
- Restart the API server

### Issue: Cannot download files

**Solution:**
- Verify job completed successfully
- Check workspace directory exists
- Ensure proper file permissions

## Architecture Details

### Job Workflow

```
1. Client uploads file → /api/upload
2. Server creates job_id, saves file
3. Client starts analysis → /api/analyze/{job_id}
4. Server queues job in ThreadPoolExecutor
5. Pipeline runner executes 10 stages
6. Results saved to workspace
7. Client checks status → /api/status/{job_id}
8. Client retrieves results → /api/results/{job_id}
9. Client downloads files → /api/download/...
```

### File Structure

```
workspace/
  job-abc123/
    input/
      design.v
      design_verilog.v
    output/
      stage1_parsing.json
      stage4_report.json
      stage8_comprehensive_report.json
      patched_fsm.v
      fsm_report.json
      fsm_report.txt
    results.json

uploads/
  job-abc123/
    design.v
```

## Security Considerations

### Production Deployment

1. **Authentication**: Add JWT/API key authentication
2. **Rate Limiting**: Implement request rate limits
3. **File Validation**: Strict input validation and sanitization
4. **CORS**: Restrict origins to trusted domains
5. **HTTPS**: Use TLS/SSL in production
6. **Job Quotas**: Limit jobs per user/IP

### Example Security Enhancement

```python
from fastapi.security import HTTPBearer
from fastapi import Depends

security = HTTPBearer()

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    token: str = Depends(security)
):
    # Verify token
    verify_token(token)
    # ... rest of upload logic
```

## Support

For issues or questions:
- GitHub: [FSMGuard Repository]
- Email: support@fsmguard.com
- Docs: http://localhost:8000/docs

## License

[Your License Here]
