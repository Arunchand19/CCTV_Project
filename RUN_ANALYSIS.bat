@echo off
echo ============================================================
echo Store Intelligence Challenge - CCTV Analytics
echo Purplle Tech Challenge 2026 - Round 2
echo ============================================================
echo.

echo Checking Python installation...
python --version
if errorlevel 1 (
    echo Python is not installed or not in PATH!
    pause
    exit /b 1
)
echo.

echo Installing dependencies...
python -m pip install -r requirements.txt
echo.

echo Running Complete Analysis Pipeline...
python run_analysis.py
echo.

echo ============================================================
echo COMPLETE!
echo ============================================================
echo Open output\store_intelligence_report.html to view results
echo.
pause
