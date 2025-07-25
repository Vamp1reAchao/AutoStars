@echo off
echo ========================================
echo    🌟 AutoStars MSBuild Builder 🌟
echo ========================================

echo Detecting MSBuild...

REM Try Visual Studio 2022
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe" (
    set MSBUILD="C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe"
    echo Found Visual Studio 2022 MSBuild
    goto :build
)

REM Try Visual Studio 2019
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe" (
    set MSBUILD="C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
    echo Found Visual Studio 2019 MSBuild
    goto :build
)

REM Try .NET Framework MSBuild
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe" (
    set MSBUILD="C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe"
    echo Found Visual Studio 2019 Community MSBuild
    goto :build
)

REM Try .NET Framework MSBuild
if exist "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\MSBuild.exe" (
    set MSBUILD="C:\Windows\Microsoft.NET\Framework64\v4.0.30319\MSBuild.exe"
    echo Found .NET Framework MSBuild
    goto :build
)

REM Try older MSBuild
if exist "C:\Program Files (x86)\MSBuild\14.0\Bin\MSBuild.exe" (
    set MSBUILD="C:\Program Files (x86)\MSBuild\14.0\Bin\MSBuild.exe"
    echo Found MSBuild 14.0
    goto :build
)

REM Try MSBuild 15.0
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\MSBuild\15.0\Bin\MSBuild.exe" (
    set MSBUILD="C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\MSBuild\15.0\Bin\MSBuild.exe"
    echo Found MSBuild 15.0
    goto :build
)

echo ❌ MSBuild not found!
echo.
echo Available options:
echo 1. Install Visual Studio Community (free): https://visualstudio.microsoft.com/downloads/
echo 2. Install Build Tools: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
echo 3. Or use Python version: python gui.py
echo.
pause
exit /b 1

:build
echo Downloading Newtonsoft.Json...
if not exist "packages" mkdir packages
if not exist "packages\Newtonsoft.Json.13.0.3" (
    powershell -Command "Invoke-WebRequest -Uri 'https://www.nuget.org/api/v2/package/Newtonsoft.Json/13.0.3' -OutFile 'packages\newtonsoft.zip'"
    powershell -Command "Expand-Archive -Path 'packages\newtonsoft.zip' -DestinationPath 'packages\Newtonsoft.Json.13.0.3' -Force"
    del "packages\newtonsoft.zip"
)

echo Building AutoStars WPF...
cd WpfApp2\WpfApp2

%MSBUILD% WpfApp2.csproj /p:Configuration=Release /p:Platform="Any CPU" /p:OutputPath=bin\Release\

if exist "bin\Release\AutoStars.exe" (
    echo Copying resources...
    copy "..\..\config.json" "bin\Release\" 2>nul
    copy "..\..\photo.png" "bin\Release\" 2>nul
    copy "..\..\logo.png" "bin\Release\" 2>nul
    
    echo ========================================
    echo ✅ Build completed successfully!
    echo 📁 Output: WpfApp2\WpfApp2\bin\Release\AutoStars.exe
    echo 🚀 Starting AutoStars...
    echo ========================================
    
    start bin\Release\AutoStars.exe
) else (
    echo ❌ Build failed!
    echo Check MSBuild output above for errors
)

cd ..\..
pause