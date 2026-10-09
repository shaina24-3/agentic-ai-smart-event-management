@echo off
setlocal
cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" -c "import uvicorn" >nul 2>&1
    if not errorlevel 1 set "PYTHON_EXE=venv\Scripts\python.exe"
)

if not defined PYTHON_EXE if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" -c "import uvicorn" >nul 2>&1
    if not errorlevel 1 set "PYTHON_EXE=..\.venv\Scripts\python.exe"
)

if not defined PYTHON_EXE set "PYTHON_EXE=python"

echo Starting backend with %PYTHON_EXE%
"%PYTHON_EXE%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
exit /b %errorlevel%
