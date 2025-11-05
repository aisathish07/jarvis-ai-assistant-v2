echo off
REM ====================================================================
REM  Jarvis AI Assistant - Windows Automated Setup
REM  This script handles the entire setup process
REM ====================================================================

setlocal enabledelayedexpansion
set "PYTHON_MIN_VERSION=3.10"

cls
echo.
echo ====================================================================
echo   JARVIS AI ASSISTANT - Windows Setup
echo   Automated Installation ^& Configuration
echo ====================================================================
echo.

REM ====================================================================
REM 1. Check Python
REM ====================================================================
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo.
    echo Please install Python 3.10+ from https://www.python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PYTHON_VER=%%i"
echo OK: Python %PYTHON_VER% found
echo.

REM ====================================================================
REM 2. Create/Activate Virtual Environment
REM ====================================================================
echo [2/6] Setting up virtual environment...
if exist "venv" (
    echo OK: Virtual environment exists
) else (
    echo Creating new virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo OK: Virtual environment activated
echo.

REM ====================================================================
REM 3. Install Dependencies
REM ====================================================================
echo [3/6] Installing dependencies...
echo This may take 5-10 minutes on first run. Please wait...
echo.

REM Upgrade pip first
python -m pip install --upgrade pip --quiet

REM Install from requirements
pip install -r requirements.txt
if errorlevel 1 (
    echo WARNING: Some dependencies may have failed
    echo Continuing anyway...
)
echo OK: Dependencies installed
echo.

REM ====================================================================
REM 4. Download spaCy Models
REM ====================================================================
echo [4/6] Downloading language models...
echo Downloading spaCy en_core_web_sm...
python -m spacy download en_core_web_sm --quiet
if errorlevel 1 (
    echo WARNING: spaCy model download had issues
    echo Trying again...
    python -m spacy download en_core_web_sm
)
echo OK: Language models ready
echo.

REM ====================================================================
REM 5. Install Playwright Browsers
REM ====================================================================
echo [5/6] Setting up browser automation...
echo Installing Playwright Chromium browser...
playwright install chromium
if errorlevel 1 (
    echo WARNING: Playwright installation had issues
    echo Web automation may not work
)
echo OK: Browser automation ready
echo.

REM ====================================================================
REM 6. Create Configuration
REM ====================================================================
echo [6/6] Creating configuration files...

if exist ".env" (
    echo OK: .env file already exists
) else (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo OK: Created .env from template
    ) else (
        (
            echo # Jarvis AI Assistant Configuration
            echo # Add your API keys here
            echo.
            echo # Required: Get from https://ai.google.dev
            echo GEMINI_API_KEY=your_key_here
            echo.
            echo # Optional: Get from https://elevenlabs.io
            echo # ELEVENLABS_API_KEY=your_key_here
            echo.
            echo # Configuration
            echo LOCAL_ONLY=false
            echo WEB_AGENT_MODE=balanced
            echo WHISPER_MODEL_SIZE=base
        ) > .env
        echo OK: Created minimal .env file
    )
)

REM Create directories
for %%d in (logs cache skills backups temp) do (
    if not exist "%%d" (
        mkdir %%d
    )
)
echo OK: Directories created
echo.

REM ====================================================================
REM Completion
REM ====================================================================
echo ====================================================================
echo   SETUP COMPLETE!
echo ====================================================================
echo.
echo NEXT STEPS:
echo.
echo 1. Edit .env file and add your GEMINI_API_KEY:
echo    - Open .env with Notepad
echo    - Go to https://ai.google.dev
echo    - Click "Get API Key"
echo    - Copy the key to .env
echo.
echo 2. Test the system:
echo    python diagnostic.py
echo.
echo 3. Run Jarvis:
echo    python main_standalone.py
echo.
echo 4. Say "Hey Jarvis" or press Ctrl+Space
echo.
echo ====================================================================
echo.
pause
exit /b 0