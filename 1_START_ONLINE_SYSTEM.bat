@echo off
echo =========================================
echo ABIZ POS - ONLINE SYSTEM (Backend + Web)
echo =========================================
echo.
echo Installing Python dependencies...
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt
echo.
echo Starting Server...
uvicorn main:app --reload
pause
