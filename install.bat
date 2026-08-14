@echo off
cd /d "%~dp0"
echo Installing AutoStars dependencies...
python -m pip install --upgrade pip
python -m pip install "flet==0.86.1"
python -m pip install "requests>=2.31,<3"
python -m pip install --no-deps "FunPayAPI==1.1.0"
python -m pip install "aiogram==3.4.1" "httpx>=0.27,<1" "tonutils==0.5.8"
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
