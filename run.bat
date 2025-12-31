@echo off
REM Finarius - Run script for Windows
REM Activates virtual environment and starts Streamlit app

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Installing dependencies...
    call venv\Scripts\activate.bat
    pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Run Streamlit app
echo Starting Finarius...
echo App will be available at http://localhost:8501
echo.
streamlit run finarius_app\app.py

pause

