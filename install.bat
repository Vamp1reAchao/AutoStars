@echo off
cd /d "%~dp0"
echo Installing AutoStars dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Installation failed.
  echo Recommended: Python 3.12.
  pause
  exit /b 1
)
echo.
echo Installation completed.
pause
