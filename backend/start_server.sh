#!/bin/bash

# FSMGuard Backend Startup Script
# ================================

echo "======================================================================"
echo "FSMGuard Backend - Starting API Server"
echo "======================================================================"

# Change to backend directory
cd "$(dirname "$0")"
cd ..

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️  No virtual environment found"
    echo "   Consider creating one with: python3 -m venv venv"
fi

# Check dependencies
echo "🔍 Checking dependencies..."

# Check FastAPI
python3 -c "import fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ FastAPI not installed"
    echo "   Installing backend dependencies..."
    pip install -r backend/requirements.txt
fi

# Check uvicorn
python3 -c "import uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Uvicorn not installed"
    echo "   Installing backend dependencies..."
    pip install -r backend/requirements.txt
fi

# Create necessary directories
echo "📁 Creating workspace directories..."
mkdir -p workspace
mkdir -p uploads
mkdir -p logs

echo ""
echo "======================================================================"
echo "🚀 Starting FSMGuard Backend API Server"
echo "======================================================================"
echo ""
echo "📡 API Server:  http://127.0.0.1:8000"
echo "📚 API Docs:    http://127.0.0.1:8000/docs"
echo "📊 Health:      http://127.0.0.1:8000/api/health"
echo ""
echo "======================================================================"
echo ""

# Start the server
python3 backend/api.py
