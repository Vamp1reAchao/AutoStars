@echo off
echo ========================================
echo    🌟 AutoStars Fixed Builder 🌟
echo ========================================

echo Installing required packages...
pip install pyinstaller flet requests

echo Creating missing files...
if not exist "db.json" echo {} > db.json
if not exist "photo.png" copy nul photo.png >nul 2>&1
if not exist "logo.png" copy nul logo.png >nul 2>&1

echo Cleaning previous builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "*.spec" del *.spec

echo Building AutoStars GUI (this may take a few minutes)...
pyinstaller ^
    --onefile ^
    --windowed ^
    --add-data "config.json;." ^
    --collect-all flet ^
    --collect-all flet_core ^
    --hidden-import flet ^
    --hidden-import flet.core ^
    --hidden-import flet.core.page ^
    --hidden-import asyncio ^
    --icon "ico.ico" ^
    --name "AutoStars-GUI" ^
    gui.py

echo Building AutoStars Console...
pyinstaller ^
    --onefile ^
    --console ^
    --add-data "config.json;." ^
    --hidden-import requests ^
    --hidden-import json ^
    --hidden-import asyncio ^
    --icon "ico.ico" ^
    --name "AutoStars-Console" ^
    main.py

if exist "dist\AutoStars-GUI.exe" (
    echo ========================================
    echo ✅ Build completed successfully!
    echo 📁 GUI: dist\AutoStars-GUI.exe
    echo 📁 Console: dist\AutoStars-Console.exe
    echo ========================================
) else (
    echo ❌ Build failed! Check output above for errors.
)

pause