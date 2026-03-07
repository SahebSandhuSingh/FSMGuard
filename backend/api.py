import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


origins = [
    "http://localhost:5173", # Standard Vite/React port
    "http://127.0.0.1:5173",
]
# --- DYNAMIC PATH SETUP ---
# This ensures Python can find 'rl_folder' and its contents
current_file_path = os.path.abspath(__file__)
backend_dir = os.path.dirname(current_file_path)
root_dir = os.path.dirname(backend_dir)
rl_dir = os.path.join(root_dir, "rl_folder")

# Add paths so Python can see everything
for path in [root_dir, rl_dir]:
    if path not in sys.path:
        sys.path.append(path)

# --- IMPORTS ---
try:
    from rl_folder.test_agent import run_model
    print("✅ Successfully imported RL model components.")
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print(f"Looked in: {sys.path}")
    sys.exit(1)

# --- APP SETUP ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "Backend is running!"}

@app.get("/analyze")
def analyze():
    try:
        result = run_model()
        return {"analysis": result}
    except Exception as e:
        return {"error": str(e)}

# --- THE LAUNCHER (This keeps the program from exiting) ---
if __name__ == "__main__":
    print("🚀 Starting FastAPI server on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)