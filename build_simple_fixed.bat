@echo off
echo ========================================
echo   🌟 AutoStars Simple Fixed Builder 🌟
echo ========================================

echo Downloading Newtonsoft.Json...
if not exist "packages" mkdir packages
if not exist "packages\Newtonsoft.Json.13.0.3" (
    powershell -Command "Invoke-WebRequest -Uri 'https://www.nuget.org/api/v2/package/Newtonsoft.Json/13.0.3' -OutFile 'packages\newtonsoft.zip'"
    powershell -Command "Expand-Archive -Path 'packages\newtonsoft.zip' -DestinationPath 'packages\Newtonsoft.Json.13.0.3' -Force"
    del "packages\newtonsoft.zip"
)

echo Creating SimpleAutoStars.cs...
(
echo using System;
echo using System.Windows;
echo using System.Windows.Controls;
echo using System.Windows.Media;
echo using System.Windows.Input;
echo using System.Diagnostics;
echo using System.IO;
echo using Newtonsoft.Json;
echo.
echo namespace SimpleAutoStars
echo {
echo     public class Program
echo     {
echo         [STAThread]
echo         public static void Main^(^)
echo         {
echo             Application app = new Application^(^);
echo             app.Run^(new MainWindow^(^)^);
echo         }
echo     }
echo.
echo     public class MainWindow : Window
echo     {
echo         private Button startBtn, stopBtn, settingsBtn;
echo         private TextBlock statusText;
echo         private bool isRunning = false;
echo.
echo         public MainWindow^(^)
echo         {
echo             Title = "🌟 AutoStars - Quantum Control";
echo             Width = 800;
echo             Height = 600;
echo             WindowStartupLocation = WindowStartupLocation.CenterScreen;
echo             Background = new SolidColorBrush^(Color.FromRgb^(10, 10, 10^)^);
echo             CreateUI^(^);
echo         }
echo.
echo         private void CreateUI^(^)
echo         {
echo             Grid grid = new Grid^(^);
echo             grid.Margin = new Thickness^(20^);
echo.
echo             TextBlock title = new TextBlock^(^);
echo             title.Text = "🚀 AUTOSTARS CONTROL MATRIX";
echo             title.FontSize = 24;
echo             title.FontWeight = FontWeights.Bold;
echo             title.Foreground = new SolidColorBrush^(Color.FromRgb^(0, 245, 255^)^);
echo             title.HorizontalAlignment = HorizontalAlignment.Center;
echo             title.Margin = new Thickness^(0, 20, 0, 40^);
echo.
echo             statusText = new TextBlock^(^);
echo             statusText.Text = "СИСТЕМА ОСТАНОВЛЕНА";
echo             statusText.FontSize = 16;
echo             statusText.FontWeight = FontWeights.Bold;
echo             statusText.Foreground = new SolidColorBrush^(Colors.Red^);
echo             statusText.HorizontalAlignment = HorizontalAlignment.Center;
echo             statusText.Margin = new Thickness^(0, 80, 0, 30^);
echo.
echo             StackPanel buttonPanel = new StackPanel^(^);
echo             buttonPanel.Orientation = Orientation.Horizontal;
echo             buttonPanel.HorizontalAlignment = HorizontalAlignment.Center;
echo             buttonPanel.Margin = new Thickness^(0, 120, 0, 0^);
echo.
echo             startBtn = CreateButton^("🚀 ЗАПУСК", StartBot^);
echo             stopBtn = CreateButton^("⏹ СТОП", StopBot^);
echo             settingsBtn = CreateButton^("⚙️ НАСТРОЙКИ", OpenSettings^);
echo.
echo             stopBtn.IsEnabled = false;
echo.
echo             buttonPanel.Children.Add^(startBtn^);
echo             buttonPanel.Children.Add^(stopBtn^);
echo             buttonPanel.Children.Add^(settingsBtn^);
echo.
echo             grid.Children.Add^(title^);
echo             grid.Children.Add^(statusText^);
echo             grid.Children.Add^(buttonPanel^);
echo.
echo             Content = grid;
echo         }
echo.
echo         private Button CreateButton^(string text, RoutedEventHandler handler^)
echo         {
echo             Button btn = new Button^(^);
echo             btn.Content = text;
echo             btn.Width = 150;
echo             btn.Height = 40;
echo             btn.Margin = new Thickness^(10^);
echo             btn.FontWeight = FontWeights.Bold;
echo             btn.Background = new SolidColorBrush^(Color.FromRgb^(0, 245, 255^)^);
echo             btn.Foreground = new SolidColorBrush^(Colors.White^);
echo             btn.BorderThickness = new Thickness^(0^);
echo             btn.Click += handler;
echo             return btn;
echo         }
echo.
echo         private void StartBot^(object sender, RoutedEventArgs e^)
echo         {
echo             isRunning = true;
echo             statusText.Text = "СИСТЕМА АКТИВНА";
echo             statusText.Foreground = new SolidColorBrush^(Colors.LimeGreen^);
echo             startBtn.IsEnabled = false;
echo             stopBtn.IsEnabled = true;
echo             MessageBox.Show^("🚀 Система запущена!", "AutoStars"^);
echo         }
echo.
echo         private void StopBot^(object sender, RoutedEventArgs e^)
echo         {
echo             isRunning = false;
echo             statusText.Text = "СИСТЕМА ОСТАНОВЛЕНА";
echo             statusText.Foreground = new SolidColorBrush^(Colors.Red^);
echo             startBtn.IsEnabled = true;
echo             stopBtn.IsEnabled = false;
echo             MessageBox.Show^("⏹ Система остановлена", "AutoStars"^);
echo         }
echo.
echo         private void OpenSettings^(object sender, RoutedEventArgs e^)
echo         {
echo             MessageBox.Show^("⚙️ Настройки будут добавлены в следующей версии", "AutoStars"^);
echo         }
echo     }
echo }
) > SimpleAutoStars.cs

echo Adding .NET to PATH...
set PATH=%PATH%;C:\Windows\Microsoft.NET\Framework64\v4.0.30319

echo Compiling Simple AutoStars...
csc /target:winexe ^
    /reference:"packages\Newtonsoft.Json.13.0.3\lib\net45\Newtonsoft.Json.dll" ^
    /reference:"C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.8.1\PresentationCore.dll" ^
    /reference:"C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.8.1\PresentationFramework.dll" ^
    /reference:"C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.8.1\WindowsBase.dll" ^
    /reference:"C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.8.1\System.Xaml.dll" ^
    /out:SimpleAutoStars.exe ^
    SimpleAutoStars.cs

if exist "SimpleAutoStars.exe" (
    echo Copying resources...
    copy "config.json" . 2>nul
    copy "photo.png" . 2>nul
    copy "logo.png" . 2>nul
    copy "packages\Newtonsoft.Json.13.0.3\lib\net45\Newtonsoft.Json.dll" . 2>nul
    
    echo ========================================
    echo ✅ Build completed successfully!
    echo 📁 Output: SimpleAutoStars.exe
    echo 🚀 Starting Simple AutoStars...
    echo ========================================
    
    start SimpleAutoStars.exe
) else (
    echo ❌ Build failed!
    echo Check compiler output above
)

pause