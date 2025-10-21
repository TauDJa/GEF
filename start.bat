@echo off
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting Flask server on http://127.0.0.1:5000
python -m flask run