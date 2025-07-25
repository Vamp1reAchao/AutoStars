@echo off
echo ========================================
echo    GitHub Upload Script
echo ========================================

echo Checking Git installation...
git --version >nul 2>&1
if errorlevel 1 (
    echo Git is not installed! Please install Git first:
    echo https://git-scm.com/download/win
    pause
    exit /b 1
)

echo Initializing Git repository...
git init

echo Enter your GitHub repository URL:
set /p repo_url=

echo Adding remote repository...
git remote add origin %repo_url%

echo Adding files...
git add .

echo Creating commit...
git commit -m "Initial commit - AutoStars project"

echo Pushing to GitHub...
git branch -M main
git push -u origin main

echo ========================================
echo Project uploaded to GitHub successfully!
echo ========================================
pause