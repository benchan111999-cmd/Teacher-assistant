@echo off
set PYTHONIOENCODING=utf-8
chcp 65001 >nul
cd /d C:\Projects\Teacher-assistant\backend
python -X utf8 -c "import sys; sys.path.insert(0, '.'); from app.main import app; print('BACKEND_LOADED')" 2>&1
if errorlevel 1 (
    echo FAILED
) else (
    echo SUCCESS
)
pause