@echo off
chcp 65001 >nul 2>&1
cd /d C:\Projects\Teacher-assistant\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info
pause