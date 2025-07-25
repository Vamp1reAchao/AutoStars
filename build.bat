@echo off
echo Installing PyInstaller...
pip install pyinstaller

echo Creating missing files...
if not exist "db.json" echo {} > db.json
if not exist "photo.png" echo. > photo.png
if not exist "logo.png" echo. > logo.png

echo Building AutoStars GUI...
pyinstaller --onefile --windowed --add-data "config.json;." --hidden-import="flet" --hidden-import="flet.core" --collect-all flet --icon="ico.ico" --name="AutoStars" gui.py

echo Building AutoStars Console...
pyinstaller --onefile --add-data "config.json;." --hidden-import="requests" --hidden-import="json" --icon="ico.ico" --name="AutoStars-Console" main.py

echo Build complete! Check 'dist' folder for executables.
pause