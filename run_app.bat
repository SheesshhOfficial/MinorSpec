@echo off
setlocal enabledelayedexpansion

title Evolutionary Market Lab - Streamlit Dashboard

echo ===============================================================================
echo                EVOLUTIONARY MARKET LAB - LAUNCHER
echo ===============================================================================
echo.

:: Change directory to the root of the project
cd /d "%~dp0"

:: Check if python is available
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found in your system PATH!
    echo Please install Python 3.10+ or ensure it is added to your environment variables.
    echo.
    pause
    exit /b 1
)

:: Verify all dashboard imports, not just Streamlit.
python -m scripts.check_runtime_dependencies
if errorlevel 1 (
    echo [WARNING] Dashboard dependencies are missing or cannot be imported.
    echo Attempting to install project dependencies from requirements.txt...
    echo.
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install required packages.
        pause
        exit /b 1
    )
    python -m scripts.check_runtime_dependencies
    if errorlevel 1 (
        echo [ERROR] Dependencies still cannot be imported. Review the errors above.
        pause
        exit /b 1
    )
)

echo [INFO] Starting Evolutionary Market Lab at http://localhost:8501...
echo [INFO] Press Ctrl+C in this terminal window to stop the server anytime.
echo.

:: Launch Streamlit app and open browser
python -m streamlit run app.py --server.port 8501

if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with an error code: !ERRORLEVEL!
    pause
)

endlocal

