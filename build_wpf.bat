@echo off
echo ========================================
echo    🌟 AutoStars WPF Builder 🌟
echo ========================================

cd /d "WpfApp2"

echo Installing NuGet packages...
nuget restore WpfApp2.sln

echo Building AutoStars WPF GUI...
"C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe" WpfApp2.sln /p:Configuration=Release /p:Platform="Any CPU"

if not exist "WpfApp2\bin\Release" (
    echo Trying alternative build path...
    "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe" WpfApp2.sln /p:Configuration=Release /p:Platform="Any CPU"
)

if not exist "WpfApp2\bin\Release" (
    echo Trying .NET Framework build...
    "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\MSBuild.exe" WpfApp2.sln /p:Configuration=Release /p:Platform="Any CPU"
)

echo Copying resources...
if exist "WpfApp2\bin\Release" (
    copy "..\config.json" "WpfApp2\bin\Release\" 2>nul
    copy "..\photo.png" "WpfApp2\bin\Release\" 2>nul
    copy "..\logo.png" "WpfApp2\bin\Release\" 2>nul
    
    echo ========================================
    echo ✅ Build completed successfully!
    echo 📁 Output: WpfApp2\WpfApp2\bin\Release\
    echo 🚀 Run: WpfApp2.exe
    echo ========================================
) else (
    echo ❌ Build failed! Please install Visual Studio or .NET Framework SDK
    echo 
    echo Alternative: Install Visual Studio Community 2022
    echo https://visualstudio.microsoft.com/downloads/
)

pause