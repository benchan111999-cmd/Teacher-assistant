import socket
import threading
import os
import sys

os.chdir(r"C:\Projects\Teacher-assistant\backend")

# Try to load the app first
try:
    from app.main import app
    APP_LOADED = True
    print("App loaded successfully")
except Exception as e:
    APP_LOADED = False
    print(f"App load error: {e}")

# Simple HTTP server that wraps the FastAPI app
if APP_LOADED:
    from hypercorn.config import Config
    from hypercorn.asgi import ASGIApp
    
    config = Config()
    config.bind = ["127.0.0.1:8000"]
    app_wrapper = ASGIApp(app)
    
    print("Starting backend on http://127.0.0.1:8000")
    from hypercorn.tornado import serve
    
    # Note: This is a blocking call
    serve(app_wrapper, config)