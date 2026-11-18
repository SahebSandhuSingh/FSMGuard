#!/usr/bin/env python3
"""
FSMGuard Backend Test Suite
============================
Test the complete backend API functionality.
"""

import requests
import time
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    print("✅ Health check passed")
    return True

def test_upload_file():
    """Test file upload"""
    print("\n📤 Testing file upload...")
    
    # Use test file
    test_file = Path(__file__).parent.parent / "input" / "dma_timing_control_verilog.v"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return None
    
    with open(test_file, "rb") as f:
        files = {"file": (test_file.name, f, "text/plain")}
        response = requests.post(f"{BASE_URL}/api/upload", files=files)
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    job_id = data["job_id"]
    print(f"✅ File uploaded successfully")
    print(f"   Job ID: {job_id}")
    print(f"   Filename: {data['filename']}")
    print(f"   Size: {data['size']} bytes")
    
    return job_id

def test_start_analysis(job_id):
    """Test starting analysis"""
    print(f"\n🚀 Starting analysis for job {job_id}...")
    
    response = requests.post(f"{BASE_URL}/api/analyze/{job_id}")
    
    if response.status_code != 200:
        print(f"❌ Analysis start failed: {response.status_code}")
        print(response.text)
        return False
    
    data = response.json()
    print(f"✅ Analysis started")
    print(f"   Status: {data['status']}")
    print(f"   Message: {data['message']}")
    
    return True

def test_check_status(job_id, wait_for_completion=True):
    """Test status checking"""
    print(f"\n📊 Checking status for job {job_id}...")
    
    max_wait = 300  # 5 minutes
    start_time = time.time()
    
    while True:
        response = requests.get(f"{BASE_URL}/api/status/{job_id}")
        
        if response.status_code != 200:
            print(f"❌ Status check failed: {response.status_code}")
            return None
        
        data = response.json()
        status = data["status"]
        progress = data.get("progress", 0)
        message = data.get("message", "")
        
        print(f"   Status: {status} ({progress}%) - {message}")
        
        if status == "completed":
            print("✅ Analysis completed!")
            return data
        
        if status == "failed":
            print("❌ Analysis failed!")
            return data
        
        if not wait_for_completion:
            return data
        
        # Check timeout
        if time.time() - start_time > max_wait:
            print("⏱️  Timeout waiting for completion")
            return data
        
        time.sleep(3)

def test_get_results(job_id):
    """Test getting results"""
    print(f"\n📋 Getting results for job {job_id}...")
    
    response = requests.get(f"{BASE_URL}/api/results/{job_id}")
    
    if response.status_code != 200:
        print(f"❌ Get results failed: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    print("✅ Results retrieved successfully")
    print(f"   Vulnerabilities found: {data.get('vulnerabilities_found', 0)}")
    print(f"   Vulnerabilities fixed: {data.get('vulnerabilities_fixed', 0)}")
    print(f"   Design safe: {data.get('design_safe', False)}")
    
    return data

def test_download_files(job_id):
    """Test file downloads"""
    print(f"\n💾 Testing file downloads for job {job_id}...")
    
    # Download patched file
    response = requests.get(f"{BASE_URL}/api/download/patched/{job_id}")
    if response.status_code == 200:
        print(f"✅ Patched file downloaded ({len(response.content)} bytes)")
    else:
        print(f"⚠️  Patched file not available: {response.status_code}")
    
    # Download JSON report
    response = requests.get(f"{BASE_URL}/api/download/report/{job_id}?format=json")
    if response.status_code == 200:
        print(f"✅ JSON report downloaded ({len(response.content)} bytes)")
    else:
        print(f"⚠️  JSON report not available: {response.status_code}")
    
    # Download text report
    response = requests.get(f"{BASE_URL}/api/download/report/{job_id}?format=txt")
    if response.status_code == 200:
        print(f"✅ Text report downloaded ({len(response.content)} bytes)")
    else:
        print(f"⚠️  Text report not available: {response.status_code}")
    
    return True

def test_list_jobs():
    """Test listing jobs"""
    print("\n📑 Listing all jobs...")
    
    response = requests.get(f"{BASE_URL}/api/jobs")
    
    if response.status_code != 200:
        print(f"❌ List jobs failed: {response.status_code}")
        return None
    
    data = response.json()
    print(f"✅ Found {data['total']} job(s)")
    
    for job in data["jobs"]:
        print(f"   - {job['job_id']}: {job['status']} ({job.get('progress', 0)}%)")
    
    return data

def run_complete_test():
    """Run complete test suite"""
    print("=" * 70)
    print("FSMGuard Backend API Test Suite")
    print("=" * 70)
    
    try:
        # Test 1: Health check
        if not test_health_check():
            print("\n❌ Health check failed - is the server running?")
            print("   Start server with: python3 backend/api.py")
            return False
        
        # Test 2: Upload file
        job_id = test_upload_file()
        if not job_id:
            print("\n❌ File upload failed")
            return False
        
        # Test 3: Start analysis
        if not test_start_analysis(job_id):
            print("\n❌ Analysis start failed")
            return False
        
        # Test 4: Check status (wait for completion)
        status = test_check_status(job_id, wait_for_completion=True)
        if not status:
            print("\n❌ Status check failed")
            return False
        
        # Test 5: Get results
        results = test_get_results(job_id)
        if not results:
            print("\n❌ Get results failed")
            return False
        
        # Test 6: Download files
        test_download_files(job_id)
        
        # Test 7: List jobs
        test_list_jobs()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print(f"\nTest Job ID: {job_id}")
        print(f"Keep job for inspection or delete with:")
        print(f"  curl -X DELETE {BASE_URL}/api/job/{job_id}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server")
        print("   Start server with: python3 backend/api.py")
        return False
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def quick_test():
    """Quick test - just health check and upload"""
    print("🚀 Quick Backend Test\n")
    
    try:
        # Health check
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server not responding correctly")
            return False
        
        # Upload test
        test_file = Path(__file__).parent.parent / "input" / "dma_timing_control_verilog.v"
        if test_file.exists():
            with open(test_file, "rb") as f:
                files = {"file": (test_file.name, f, "text/plain")}
                response = requests.post(f"{BASE_URL}/api/upload", files=files)
            
            if response.status_code == 200:
                job_id = response.json()["job_id"]
                print(f"✅ File upload works (Job ID: {job_id})")
                return True
            else:
                print(f"❌ Upload failed: {response.status_code}")
                return False
        else:
            print("⚠️  Test file not found, skipping upload test")
            return True
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server at", BASE_URL)
        print("   Start with: python3 backend/api.py")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        success = quick_test()
    else:
        success = run_complete_test()
    
    sys.exit(0 if success else 1)
