import os
import sys
import logging

os.chdir(r"C:\Projects\Teacher-assistant\backend")
sys.path.insert(0, ".")

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Import and run
try:
    import uvicorn
    from app.main import app
    print("Starting server...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...")
