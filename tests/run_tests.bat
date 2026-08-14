@echo off
cd /d "%~dp0.."
python -m unittest discover -s tests -v
pause
