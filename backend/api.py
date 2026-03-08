"""
FSMGuard Backend API
====================
Complete REST API for FSMGuard FSM security analysis pipeline.

Endpoints:
    - POST /api/upload - Upload Verilog file
    - POST /api/analyze/{job_id} - Start pipeline analysis
    - GET /api/status/{job_id} - Check job status
    - GET /api/results/{job_id} - Get analysis results
    - GET /api/download/patched/{job_id} - Download patched FSM
    - GET /api/download/report/{job_id} - Download security report
    - DELETE /api/job/{job_id} - Clean up job workspace
"""

import sys
import os
from pathlib import Path
import uuid
import time
import json
from typing import Dict, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.pipeline_runner import PipelineRunner

# ============================================================
# CONFIGURATION
# ============================================================

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'.v', '.sv', '.vh', '.svh'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# ============================================================
# DATA MODELS
# ============================================================

class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed
    progress: int  # 0-100
    message: Optional[str] = None
    created_at: float
    updated_at: float

class AnalysisResult(BaseModel):
    job_id: str
    status: str
    vulnerabilities_found: int
    vulnerabilities_fixed: int
    design_safe: bool
    stages: Dict[str, Any]
    files: Dict[str, str]

# ============================================================
# APP INITIALIZATION
# ============================================================

app = FastAPI(
    title="FSMGuard API",
    description="Automated FSM Security Analysis Pipeline",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pipeline runner
runner = PipelineRunner()

# Job tracking
jobs: Dict[str, JobStatus] = {}
job_results: Dict[str, Any] = {}

# Thread pool for background tasks
executor = ThreadPoolExecutor(max_workers=4)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def validate_verilog_file(filename: str) -> bool:
    """Validate file extension"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

def create_job_id() -> str:
    """Generate unique job ID"""
    return f"job-{uuid.uuid4().hex[:12]}"

def update_job_status(job_id: str, status: str, progress: int = 0, message: str = None):
    """Update job status"""
    if job_id in jobs:
        jobs[job_id].status = status
        jobs[job_id].progress = progress
        jobs[job_id].message = message
        jobs[job_id].updated_at = time.time()

def run_pipeline_async(job_id: str, input_file: Path, filename: str):
    """Run pipeline in background"""
    try:
        update_job_status(job_id, "running", 5, "Starting pipeline...")

        job_dir = runner.create_job_workspace(job_id)

        # Convert .sv if needed
        verilog_file = input_file
        if filename.endswith(".sv"):
            converted = job_dir / "input" / filename.replace(".sv", "_verilog.v")
            if runner.convert_systemverilog(input_file, converted):
                verilog_file = converted

        # Stages 1-4
        update_job_status(job_id, "running", 15, "Stages 1-4: Parsing & vulnerability detection...")
        stage14 = runner.run_stages_1_to_4(job_dir, verilog_file)

        results = {
            "job_id": job_id,
            "filename": filename,
            "workspace": str(job_dir),
            "stages": {"stage3_4": stage14},
        }

        if not stage14["success"]:
            update_job_status(job_id, "failed", 15, stage14.get("error", "Stages 1-4 failed"))
            results["status"] = "failed"
            results["error"] = stage14.get("error", "Stages 1-4 failed")
            runner.save_job_results(job_id, results)
            job_results[job_id] = results
            return

        update_job_status(job_id, "running", 50, "Detection complete. Starting patching...")

        if not stage14.get("vulnerabilities"):
            results["status"] = "completed"
            results["message"] = "No vulnerabilities detected — design is safe"
            update_job_status(job_id, "completed", 100, "No vulnerabilities found")
            runner.save_job_results(job_id, results)
            job_results[job_id] = results
            return

        # Stages 5-10
        update_job_status(job_id, "running", 55, "Stages 5-10: Patching & verification...")
        stage510 = runner.run_stages_5_to_10(job_dir, verilog_file)
        results["stages"]["stage5_10"] = stage510

        update_job_status(job_id, "running", 90, "Finalising report...")

        if stage510["success"]:
            results["status"] = "completed"
            results["patched_file"] = stage510["outputs"].get("patched_fsm.v")
            results["final_report"] = stage510["outputs"].get("fsm_report.json")
            update_job_status(job_id, "completed", 100, "Analysis complete")
        else:
            results["status"] = "partial"
            results["message"] = "Pipeline completed with warnings"
            update_job_status(job_id, "completed", 100, "Completed with warnings")

        runner.save_job_results(job_id, results)
        job_results[job_id] = results

    except Exception as e:
        update_job_status(job_id, "failed", 0, f"Error: {str(e)}")
        job_results[job_id] = {"error": str(e)}

# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "FSMGuard API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/upload",
            "analyze": "/api/analyze/{job_id}",
            "status": "/api/status/{job_id}",
            "results": "/api/results/{job_id}",
            "download_patched": "/api/download/patched/{job_id}",
            "download_report": "/api/download/report/{job_id}"
        }
    }

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "active_jobs": len([j for j in jobs.values() if j.status == "running"]),
        "total_jobs": len(jobs),
        "workspace": str(runner.workspace_dir)
    }

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload Verilog/SystemVerilog file for analysis
    
    Returns job_id for tracking the analysis
    """
    # Validate file
    if not validate_verilog_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024} MB"
        )
    
    # Create job
    job_id = create_job_id()
    
    # Save file
    upload_path = UPLOAD_DIR / job_id
    upload_path.mkdir(exist_ok=True)
    file_path = upload_path / file.filename
    
    with open(file_path, 'wb') as f:
        f.write(contents)
    
    # Create job status
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="uploaded",
        progress=0,
        message="File uploaded successfully",
        created_at=time.time(),
        updated_at=time.time()
    )
    
    return {
        "job_id": job_id,
        "filename": file.filename,
        "size": len(contents),
        "status": "uploaded",
        "message": "File uploaded. Use /api/analyze/{job_id} to start analysis."
    }

@app.post("/api/analyze/{job_id}")
async def analyze_design(job_id: str, background_tasks: BackgroundTasks):
    """
    Start FSMGuard pipeline analysis for uploaded file
    """
    # Check if job exists
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if already running
    if jobs[job_id].status == "running":
        raise HTTPException(status_code=400, detail="Analysis already in progress")
    
    # Find uploaded file
    upload_path = UPLOAD_DIR / job_id
    if not upload_path.exists():
        raise HTTPException(status_code=404, detail="Upload directory not found")
    
    files = list(upload_path.glob("*.v")) + list(upload_path.glob("*.sv"))
    if not files:
        raise HTTPException(status_code=404, detail="No Verilog file found")
    
    input_file = files[0]
    
    # Start analysis in background
    update_job_status(job_id, "pending", 0, "Analysis queued")
    background_tasks.add_task(run_pipeline_async, job_id, input_file, input_file.name)
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Analysis started. Check /api/status/{job_id} for progress."
    }

@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get current status of analysis job
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]

@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    """
    Get complete analysis results for a job
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if jobs[job_id].status != "completed":
        return {
            "job_id": job_id,
            "status": jobs[job_id].status,
            "message": "Analysis not completed yet"
        }
    
    # Get results
    if job_id in job_results:
        results = job_results[job_id]
    else:
        results = runner.get_job_results(job_id)
    
    if not results:
        raise HTTPException(status_code=404, detail="Results not found")
    
    # Format response
    final_report = results.get("stages", {}).get("stage5_10", {}).get("outputs", {}).get("fsm_report.json", {})
    
    # Build frontend-shaped vulnerability list from stage3_4 flagged states
    flagged_states = results.get("stages", {}).get("stage3_4", {}).get("vulnerabilities", [])
    severity_map = {"CRITICAL": "critical", "HIGH": "high", "MEDIUM": "medium", "LOW": "low"}
    vulnerability_list = [
        {
            "id": f"vuln-{str(i + 1).zfill(3)}",
            "title": f"{s.get('cwe', 'CWE-???')}: {s.get('cwe_label', 'Unknown')}",
            "severity": severity_map.get(s.get("severity", "").upper(), "medium"),
            "state": s.get("state_name", "unknown"),
            "description": (
                f"State \"{s.get('state_name')}\" is vulnerable "
                f"(risk score: {s.get('risk_score', 0):.3f}). "
                f"Attack path: {s.get('attack_path', 'N/A')}."
            ),
            "line": 0,
            "patchedCode": f"// {s.get('recommended_fix', 'Fix')} applied to {s.get('state_name')}",
            "solution": f"Apply {s.get('recommended_fix', 'fix')} to state {s.get('state_name')}",
        }
        for i, s in enumerate(flagged_states)
    ]

    return {
        "job_id": job_id,
        "status": results.get("status", "unknown"),
        "filename": results.get("filename"),
        "vulnerabilities_found": len(flagged_states),
        "vulnerabilities_fixed": final_report.get("vulnerabilities_fixed", 0),
        "design_safe": final_report.get("design_safe", False),
        "vulnerability_list": vulnerability_list,
        "stages": results.get("stages", {}),
        "workspace": results.get("workspace"),
        "files": {
            "patched": results.get("patched_file"),
            "report": results.get("final_report")
        }
    }

@app.get("/api/download/patched/{job_id}")
async def download_patched_file(job_id: str):
    """
    Download patched FSM Verilog file
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_dir = runner.workspace_dir / job_id
    patched_file = job_dir / "output" / "patched_fsm.v"
    
    if not patched_file.exists():
        raise HTTPException(status_code=404, detail="Patched file not found")
    
    return FileResponse(
        path=str(patched_file),
        filename=f"{job_id}_patched.v",
        media_type="text/plain"
    )

@app.get("/api/download/report/{job_id}")
async def download_report(job_id: str, format: str = "json"):
    """
    Download security report (json or txt)
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_dir = runner.workspace_dir / job_id
    
    if format == "txt":
        report_file = job_dir / "output" / "fsm_report.txt"
        media_type = "text/plain"
        filename = f"{job_id}_report.txt"
    else:
        report_file = job_dir / "output" / "fsm_report.json"
        media_type = "application/json"
        filename = f"{job_id}_report.json"
    
    if not report_file.exists():
        raise HTTPException(status_code=404, detail=f"Report file not found ({format})")
    
    return FileResponse(
        path=str(report_file),
        filename=filename,
        media_type=media_type
    )

@app.get("/api/logs/{job_id}")
async def get_job_logs(job_id: str):
    """
    Get pipeline execution logs for a job
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_id in job_results:
        results = job_results[job_id]
        stage5_10 = results.get("stages", {}).get("stage5_10", {})
        
        return {
            "job_id": job_id,
            "stdout": stage5_10.get("stdout", ""),
            "stderr": stage5_10.get("stderr", "")
        }
    
    return {"job_id": job_id, "logs": "No logs available"}

@app.delete("/api/job/{job_id}")
async def delete_job(job_id: str):
    """
    Clean up job workspace and remove from tracking
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Clean up workspace
    runner.cleanup_job(job_id)
    
    # Remove from tracking
    if job_id in jobs:
        del jobs[job_id]
    if job_id in job_results:
        del job_results[job_id]
    
    # Clean up upload directory
    upload_path = UPLOAD_DIR / job_id
    if upload_path.exists():
        import shutil
        shutil.rmtree(upload_path)
    
    return {"message": f"Job {job_id} deleted successfully"}

@app.get("/api/jobs")
async def list_jobs(status: Optional[str] = None):
    """
    List all jobs (optionally filtered by status)
    """
    filtered_jobs = jobs.values()
    
    if status:
        filtered_jobs = [j for j in filtered_jobs if j.status == status]
    
    return {
        "total": len(filtered_jobs),
        "jobs": list(filtered_jobs)
    }

# ============================================================
# STARTUP & SHUTDOWN
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("=" * 70)
    print("🚀 FSMGuard Backend API Starting...")
    print("=" * 70)
    print(f"📁 Workspace: {runner.workspace_dir}")
    print(f"📁 Uploads:   {UPLOAD_DIR}")
    print(f"🔧 Max workers: {executor._max_workers}")
    print("=" * 70)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("\n🛑 Shutting down FSMGuard API...")
    executor.shutdown(wait=True)

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 Starting FSMGuard Backend API")
    print("=" * 70)
    print("📡 Server: http://127.0.0.1:8000")
    print("📚 Docs:   http://127.0.0.1:8000/docs")
    print("=" * 70 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )