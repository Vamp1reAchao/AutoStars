@echo off
echo ========================================
echo    🌟 AutoStars Simple Builder 🌟
echo ========================================

echo Checking for .NET Framework...
where csc >nul 2>nul
if %errorlevel% neq 0 (
    echo Adding .NET Framework to PATH...
    set PATH=%PATH%;C:\Windows\Microsoft.NET\Framework64\v4.0.30319
)

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
    /reference:"C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.8.1\PresentationCore.dll" ^
    /reference:"C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.8.1\PresentationFramework.dll" ^
    /reference:"C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.8.1\WindowsBase.dll" ^
    /reference:"C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.8.1\System.Xaml.dll" ^
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
    echo 📁 Output: WpfApp2\WpfApp2\AutoStars.exe
    echo 🚀 Starting AutoStars...
    echo ========================================
    
    start AutoStars.exe
) else (
    echo ❌ Build failed! 
    echo Please install .NET Framework 4.8.1 SDK
)

cd ..\..
pause