@echo off
setlocal
cd /d "%~dp0"

python -m pip install --upgrade pyinstaller

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

flet pack gui.py --name AutoStars --icon ico.ico --add-data "photo.png;." --add-data "ico.ico;." --add-data "config.example.json;."

if errorlevel 1 (
    echo.
    echo BUILD FAILED
    pause
    exit /b 1
)

if exist config.json copy /y config.json dist\AutoStars\config.json >nul
if not exist dist\AutoStars\config.example.json copy /y config.example.json dist\AutoStars\config.example.json >nul
if not exist dist\AutoStars\ico.ico copy /y ico.ico dist\AutoStars\ico.ico >nul

echo.
echo Build completed: dist\AutoStars
pause
