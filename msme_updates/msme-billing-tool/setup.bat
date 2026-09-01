@echo off
echo ============================================
echo  MSME Billing Utility - Setup
echo ============================================
echo.
echo This will install everything needed to run the tool.
echo It only needs to be run once (or after any update).
echo.
pause

echo.
echo [1/2] Setting up backend (Python)...
cd backend
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt
call venv\Scripts\deactivate.bat
cd ..

echo.
echo [2/2] Setting up frontend (Node)...
cd frontend
call npm install
cd ..

echo.
echo ============================================
echo  Setup complete!
echo  Run start.bat to launch the application.
echo ============================================
pause
