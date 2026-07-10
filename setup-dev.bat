@echo off
REM Development environment setup script for Tender Document Extraction API (Windows)

echo ==========================================
echo Tender API - Development Setup (Windows)
echo ==========================================
echo.

REM Check if Python is installed
echo [1/7] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo ✓ Python %python_version% found
echo.

REM Create virtual environment
echo [2/7] Creating virtual environment...
if exist venv (
    echo ✓ Virtual environment already exists
) else (
    python -m venv venv
    echo ✓ Virtual environment created
)
echo.

REM Activate virtual environment
echo [3/7] Activating virtual environment...
call venv\Scripts\activate.bat
echo ✓ Virtual environment activated
echo.

REM Install dependencies
echo [4/7] Installing dependencies...
python -m pip install --upgrade pip setuptools wheel >nul
pip install -r requirements.txt >nul
echo ✓ Dependencies installed
echo.

REM Install dev dependencies
echo [5/7] Installing development dependencies...
pip install -r requirements-dev.txt >nul
echo ✓ Development dependencies installed
echo.

REM Create uploads directory
echo [6/7] Creating uploads directory...
if not exist uploads mkdir uploads
echo ✓ Uploads directory created
echo.

REM Initialize database
echo [7/7] Initializing database...
python -c "from app import create_app, db; app = create_app('development'); ctx = app.app_context(); ctx.push(); db.create_all(); print('✓ Database initialized')"
echo.

echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo To start the development server, run:
echo.
echo   venv\Scripts\activate.bat
echo   python app.py
echo.
echo Or use the manage script:
echo.
echo   python manage.py run --debug
echo.
echo The API will be available at: http://localhost:5000
echo API Documentation: http://localhost:5000/
echo.
pause
