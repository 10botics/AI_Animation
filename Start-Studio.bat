@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Python not found. Install Python 3.10+ and try again.
        pause
        exit /b 1
    )
)

echo Installing dependencies...
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)

set "STUDIO_ARGS="
if not "%~1"=="" set "STUDIO_ARGS=--port %~1"
if not "%~2"=="" (
    if defined STUDIO_ARGS (
        set "STUDIO_ARGS=%STUDIO_ARGS% --chapter %~2"
    ) else (
        set "STUDIO_ARGS=--chapter %~2"
    )
)

echo.
if defined STUDIO_ARGS (
    echo Starting AI Animation Studio with: %STUDIO_ARGS%
) else (
    echo Starting AI Animation Studio ^(port 8501, chapter from sidebar or .env^)...
    echo Examples: Start-Studio.bat 8502
    echo           Start-Studio.bat 8502 Chapter-82
)
echo Close this window to stop the dashboard.
echo.

if defined STUDIO_ARGS (
    ".venv\Scripts\python.exe" scripts\start_studio.py %STUDIO_ARGS%
) else (
    ".venv\Scripts\python.exe" scripts\start_studio.py
)

pause
