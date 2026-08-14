@echo off
cd /d "%~dp0"
python -c "import sys; print('Python:', sys.executable); print('Version:', sys.version)"
python gui.py
if errorlevel 1 pause
