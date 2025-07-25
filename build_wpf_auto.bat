@echo off
echo ========================================
echo    🌟 AutoStars Auto Builder 🌟
echo ========================================

echo Detecting .NET Framework version...

REM Check for 4.8.1 first
if exist "C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.8.1" (
    echo Found .NET Framework 4.8.1
    set NETVER=v4.8.1
    goto :build
)

REM Check for 4.8
if exist "C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.8" (
    echo Found .NET Framework 4.8
    set NETVER=v4.8
    goto :build
)

REM Check for 4.7.2
if exist "C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.7.2" (
    echo Found .NET Framework 4.7.2
    set NETVER=v4.7.2
    goto :build
)

echo ❌ .NET Framework 4.7.2+ not found!
echo Please download from: https://dotnet.microsoft.com/download/dotnet-framework
pause
exit /b 1

:build
echo Using .NET Framework %NETVER%

echo Adding .NET to PATH...
set PATH=%PATH%;C:\Windows\Microsoft.NET\Framework64\v4.0.30319

echo Downloading Newtonsoft.Json...
if not exist "packages" mkdir packages
if not exist "packages\Newtonsoft.Json.13.0.3" (
    powershell -Command "Invoke-WebRequest -Uri 'https://www.nuget.org/api/v2/package/Newtonsoft.Json/13.0.3' -OutFile 'packages\newtonsoft.zip'"
    powershell -Command "Expand-Archive -Path 'packages\newtonsoft.zip' -DestinationPath 'packages\Newtonsoft.Json.13.0.3' -Force"
    del "packages\newtonsoft.zip"
)

echo Compiling AutoStars WPF...
cd WpfApp2\WpfApp2

csc /target:winexe ^
    /reference:"..\..\packages\Newtonsoft.Json.13.0.3\lib\net45\Newtonsoft.Json.dll" ^
    /reference:"C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\%NETVER%\PresentationCore.dll" ^
    /reference:"C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\%NETVER%\PresentationFramework.dll" ^
    /reference:"C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\%NETVER%\WindowsBase.dll" ^
    /reference:"C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\%NETVER%\System.Xaml.dll" ^
    /out:AutoStars.exe ^
    *.cs

if exist "AutoStars.exe" (
    echo Copying resources...
    copy "..\..\config.json" . 2>nul
    copy "..\..\photo.png" . 2>nul
    copy "..\..\logo.png" . 2>nul
    copy "..\..\packages\Newtonsoft.Json.13.0.3\lib\net45\Newtonsoft.Json.dll" . 2>nul
    
    echo ========================================
    echo ✅ Build completed successfully!
    echo 📁 Framework: %NETVER%
    echo 🚀 Output: WpfApp2\WpfApp2\AutoStars.exe
    echo ========================================
    
    echo Starting AutoStars...
    start AutoStars.exe
) else (
    echo ❌ Build failed!
    echo Check if all .NET Framework references are available
)

cd ..\..
pause