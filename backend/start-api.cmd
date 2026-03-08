@echo off
setlocal

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

if not exist "%SCRIPT_DIR%\.venv\Scripts\python.exe" (
  echo Backend virtual environment Python was not found at "%SCRIPT_DIR%\.venv\Scripts\python.exe"
  exit /b 1
)

"%SCRIPT_DIR%\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
