@echo off
echo ===================================================
echo Starting MSME Billing & Receivable Control Tool
echo ===================================================

echo Starting FastAPI Backend Server on http://localhost:8000 ...
start "MSME Backend (FastAPI)" cmd /k "cd /d %~dp0backend && (if exist .venv\Scripts\activate.bat (call .venv\Scripts\activate.bat) else if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat)) && python scripts\upgrade_database.py && uvicorn main:app --reload --port 8000"

echo Starting React Frontend Server on http://localhost:5173 ...
start "MSME Frontend (Vite)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Both servers are launching in separate windows:
echo   - Backend API: http://localhost:8000 (Swagger docs at http://localhost:8000/docs)
echo   - Frontend UI:  http://localhost:5173
echo.
