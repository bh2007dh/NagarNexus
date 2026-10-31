@echo off
cd /d "%~dp0"
echo ============================================================================
echo   NAGARNEXUS - AI-Powered Hyperlocal Urban Intelligence Platform
echo ============================================================================
echo Starting Backend API Server on http://127.0.0.1:8000 ...
start "NagarNexus Backend" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting Frontend Vite Server on http://localhost:5173 ...
start "NagarNexus Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo Both servers launched! Open http://localhost:5173 or http://127.0.0.1:8000 in your browser.

