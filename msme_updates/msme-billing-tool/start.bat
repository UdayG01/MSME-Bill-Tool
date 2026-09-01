@echo off
echo ============================================
echo  MSME Billing Utility - Starting...
echo ============================================
echo.

start "MSME Billing - Backend" cmd /k "cd backend && call venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

start "MSME Billing - Frontend" cmd /k "cd frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo Both servers are starting in separate windows.
echo Once ready, open your browser to: http://localhost:5173
echo.
echo To stop the application, close both command windows.
echo ============================================
start http://localhost:5173
pause
