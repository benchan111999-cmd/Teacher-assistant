import os
import sys

os.chdir(r"C:\Projects\Teacher-assistant\backend")
sys.path.insert(0, ".")

# Run uvicorn directly without CREATE_NO_WINDOW
import uvicorn
from app.main import app

print("Starting backend server...")
uvicorn.run(app, host="127.0.0.1", port=8000)