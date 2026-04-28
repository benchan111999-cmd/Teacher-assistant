import sys
import os
import requests

base_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(base_dir, 'backend')
site_pkgs_dir = os.path.join(base_dir, 'Lib', 'site-packages')

sys.path.insert(0, backend_dir)
sys.path.insert(0, site_pkgs_dir)

os.chdir(backend_dir)

import uvicorn
from app.main import app

# Create log file
log_file = open('backend.log', 'w', encoding='utf-8')
sys.stdout = log_file
sys.stderr = log_file

print("=" * 50)
print("Starting Teacher Assistant Backend on http://127.0.0.1:8000")
print("=" * 50)

uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")