#!/usr/bin/env python
"""Direct startup script that logs to file"""
import os
import sys

# Change to backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Redirect output
log_file = open('server.log', 'w', encoding='utf-8')
sys.stdout = log_file
sys.stderr = log_file

print("=" * 50, flush=True)
print("Starting Teacher Assistant Backend", flush=True)
print("=" * 50, flush=True)

try:
    import uvicorn
    from app.main import app
    
    print("App loaded successfully", flush=True)
    print("Starting server on http://127.0.0.1:8000", flush=True)
    print("=" * 50, flush=True)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc()
finally:
    log_file.close()