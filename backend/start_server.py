import logging
import sys
import os

os.chdir(r"C:\Projects\Teacher-assistant\backend")
logging.basicConfig(level=logging.DEBUG, filename="server_log.txt", mode="w", format="%(message)s")
sys.stdout = open("server_stdout.txt", "w")
sys.stderr = sys.stdout

try:
    import uvicorn
    from app.main import app
    
    print("=" * 50, flush=True)
    print("STARTING SERVER", flush=True)
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
    sys.stdout.close()