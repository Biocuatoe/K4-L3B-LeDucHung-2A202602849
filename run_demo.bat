@echo off
REM ============================================================
REM run_demo.bat — K4-L3B Shopee Policy RAG Demo launcher
REM Usage: double-click this file, or run from repo root:
REM   .\run_demo.bat
REM ============================================================

cd /d "%~dp0"

echo.
echo ============================================================
echo  K4-L3B Shopee Policy RAG Demo
echo  Opening at http://127.0.0.1:7860
echo  Press Ctrl+C to stop
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11+ from python.org
    pause
    exit /b 1
)

REM Check GROQ_API_KEY
where python >nul 2>&1
for /f "tokens=1,2 delims==" %%A in ('python -c "import os; print(f'GROQ_API_KEY={os.getenv(''GROQ_API_KEY'',''NOTSET'')}')" 2^>nul') do (
    if "%%A"=="GROQ_API_KEY" (
        if "%%B"=="NOTSET" (
            echo WARNING: GROQ_API_KEY not set.
            echo   Get a free key at: https://console.groq.com
            echo   Add to .env file: GROQ_API_KEY=your_key_here
            echo.
        ) else (
            echo GROQ_API_KEY: OK
        )
    )
)

REM Check dependencies
python -c "import gradio" >nul 2>&1
if errorlevel 1 (
    echo WARNING: gradio not installed.
    echo   Run: pip install gradio groq sentence-transformers python-dotenv
    echo.
)

echo Starting app.py...
python app.py

if errorlevel 1 (
    echo.
    echo ERROR: app.py exited with code %errorlevel%
    pause
)
