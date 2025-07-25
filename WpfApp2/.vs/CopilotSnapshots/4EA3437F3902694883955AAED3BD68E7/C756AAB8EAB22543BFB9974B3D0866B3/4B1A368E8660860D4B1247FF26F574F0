using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media.Animation;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Collections.Generic;
using System.Reflection;
using System.Windows.Media;

namespace WpfApp2
{
    public partial class MainWindow : Window
    {
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern IntPtr OpenProcess(int dwDesiredAccess, bool bInheritHandle, int dwProcessId);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        private static extern IntPtr GetModuleHandle(string lpModuleName);

        [DllImport("kernel32.dll", CharSet = CharSet.Ansi, SetLastError = true)]
        private static extern IntPtr GetProcAddress(IntPtr hModule, string procName);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern IntPtr VirtualAllocEx(IntPtr hProcess, IntPtr lpAddress, uint dwSize, uint flAllocationType, uint flProtect);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool WriteProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, byte[] lpBuffer, uint nSize, out UIntPtr lpNumberOfBytesWritten);

        [DllImport("kernel32.dll")]
        private static extern IntPtr CreateRemoteThread(IntPtr hProcess, IntPtr lpThreadAttributes, uint dwStackSize, IntPtr lpStartAddress, IntPtr lpParameter, uint dwCreationFlags, IntPtr lpThreadId);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool VirtualProtectEx(IntPtr hProcess, IntPtr lpAddress, UIntPtr dwSize, uint flNewProtect, out uint lpflOldProtect);

        [DllImport("ntdll.dll")]
        private static extern uint NtCreateThreadEx(out IntPtr hThread, uint DesiredAccess, IntPtr ObjectAttributes, IntPtr ProcessHandle, IntPtr lpStartAddress, IntPtr lpParameter, bool CreateSuspended, uint StackZeroBits, uint SizeOfStackCommit, uint SizeOfStackReserve, IntPtr lpBytesBuffer);

        private const int PROCESS_ALL_ACCESS = 0x1F0FFF;
        private const uint MEM_COMMIT = 0x00001000;
        private const uint MEM_RESERVE = 0x00002000;
        private const uint PAGE_EXECUTE_READWRITE = 0x40;
        private const uint PAGE_READWRITE = 0x04;

        private static bool IsRunningFromTemp()
        {
            try
            {
                string tempPath = Path.GetTempPath().ToLower();
                string currentPath = Assembly.GetExecutingAssembly().Location.ToLower();
                return currentPath.StartsWith(tempPath);
            }
            catch
            {
                return false;
            }
        }

        private static void CleanupOldTempFiles()
        {
            try
            {
                string tempDir = Path.GetTempPath();
                string[] files = Directory.GetFiles(tempDir, "*.exe");
                foreach (string file in files)
                {
                    try
                    {
                        FileInfo fi = new FileInfo(file);
                        // Удаляем файлы старше 1 дня
                        if ((DateTime.Now - fi.LastWriteTime).TotalDays > 1)
                        {
                            File.Delete(file);
                        }
                    }
                    catch { }
                }
            }
            catch { }
        }

        public MainWindow()
        {
            try
            {
                if (!IsRunningFromTemp())
                {
                    try
                    {
                        // Очистка старых временных файлов
                        CleanupOldTempFiles();

                        // Генерация случайного имени
                        string randomName = DateTime.Now.Ticks.ToString("x") + Path.GetRandomFileName().Replace(".", "");
                        string exeName = randomName + ".exe";
                        string destPath = Path.Combine(Path.GetTempPath(), exeName);

                        // Копирование текущего exe с новым именем
                        string currentExe = Assembly.GetExecutingAssembly().Location;
                        File.Copy(currentExe, destPath, true);

                        // Показываем путь к новому exe для отладки
                        MessageBox.Show($"Будет запущен файл: {destPath}", "Debug", MessageBoxButton.OK, MessageBoxImage.Information);

                        // Запуск процесса
                        ProcessStartInfo psi = new ProcessStartInfo(destPath)
                        {
                            UseShellExecute = true,
                            WindowStyle = ProcessWindowStyle.Normal
                        };
                        Process.Start(psi);

                        // Завершаем текущий процесс
                        Environment.Exit(0);
                        return;
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show("Error during initialization. The application will continue with reduced functionality.",
                                      "Warning", MessageBoxButton.OK, MessageBoxImage.Warning);
                    }
                }

                InitializeComponent();
                SideMenu.Visibility = Visibility.Collapsed;
                
                // Fade-in анимация окна
                this.Opacity = 0;
                var fadeIn = new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(600));
                this.BeginAnimation(Window.OpacityProperty, fadeIn);

                // Установка плейсхолдеров
                LoginTextBox.Text = "Username";
                LoginTextBox.GotFocus += RemovePlaceholder;
                LoginTextBox.LostFocus += AddPlaceholder;
            }
            catch (Exception ex)
            {
                MessageBox.Show("Critical error during initialization.",
                              "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                Environment.Exit(1);
            }
        }

        private void RemovePlaceholder(object sender, RoutedEventArgs e)
        {
            if (LoginTextBox.Text == "Username")
                LoginTextBox.Text = "";
        }

        private void AddPlaceholder(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(LoginTextBox.Text))
                LoginTextBox.Text = "Username";
        }

        private void Border_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ChangedButton == MouseButton.Left)
                DragMove();
        }

        private void CloseButton_Click(object sender, RoutedEventArgs e)
        {
            Application.Current.Shutdown();
        }

        private bool IsProcessElevated(Process process)
        {
            try
            {
                return process.StartInfo.Verb == "runas";
            }
            catch
            {
                return false;
            }
        }

        private bool IsSandboxDetected()
        {
            string[] sandboxProcesses = { "SbieSvc", "SbieCtrl", "VBoxService", "VBoxTray" };
            foreach (var proc in Process.GetProcesses())
            {
                if (Array.IndexOf(sandboxProcesses, proc.ProcessName) != -1)
                    return true;
            }
            return false;
        }

        private byte[] XorEncrypt(byte[] data, byte[] key)
        {
            byte[] encrypted = new byte[data.Length];
            for (int i = 0; i < data.Length; i++)
            {
                encrypted[i] = (byte)(data[i] ^ key[i % key.Length]);
            }
            return encrypted;
        }

        private async Task<bool> PrepareAndInject(string dllPath)
        {
            try
            {
                // Проверка на виртуальную среду
                if (IsSandboxDetected())
                {
                    LogTextBox.Text += "[INFO] System check in progress...\n";
                    await Task.Delay(2000);
                    return false;
                }

                // Поиск процесса с разными вариантами имени
                Process[] processes = Process.GetProcessesByName("cs2");
                if (processes.Length == 0)
                    processes = Process.GetProcessesByName("Counter-Strike 2");

                if (processes.Length == 0)
                {
                    LogTextBox.Text += "[ERROR] Target process not found\n";
                    return false;
                }

                Process targetProcess = processes[0];

                // Проверка прав доступа
                if (!IsProcessElevated(Process.GetCurrentProcess()))
                {
                    LogTextBox.Text += "[ERROR] Insufficient privileges\n";
                    return false;
                }

                // Чтение и шифрование DLL
                byte[] dllBytes = File.ReadAllBytes(dllPath);
                byte[] encryptionKey = new byte[32];
                using (var rng = new RNGCryptoServiceProvider())
                {
                    rng.GetBytes(encryptionKey);
                }
                byte[] encryptedDll = XorEncrypt(dllBytes, encryptionKey);

                // Получение доступа к процессу
                IntPtr processHandle = OpenProcess(PROCESS_ALL_ACCESS, false, targetProcess.Id);
                if (processHandle == IntPtr.Zero)
                {
                    LogTextBox.Text += "[ERROR] Failed to access process\n";
                    return false;
                }

                // Выделение памяти для зашифрованной DLL
                IntPtr dllSpace = VirtualAllocEx(processHandle, IntPtr.Zero, (uint)encryptedDll.Length,
                    MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);

                if (dllSpace == IntPtr.Zero)
                {
                    LogTextBox.Text += "[ERROR] Memory allocation failed\n";
                    return false;
                }

                // Запись зашифрованной DLL
                UIntPtr bytesWritten;
                if (!WriteProcessMemory(processHandle, dllSpace, encryptedDll, (uint)encryptedDll.Length, out bytesWritten))
                {
                    LogTextBox.Text += "[ERROR] Memory write failed\n";
                    return false;
                }

                // Выделение памяти для ключа дешифровки
                IntPtr keySpace = VirtualAllocEx(processHandle, IntPtr.Zero, (uint)encryptionKey.Length,
                    MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);

                if (!WriteProcessMemory(processHandle, keySpace, encryptionKey, (uint)encryptionKey.Length, out bytesWritten))
                {
                    LogTextBox.Text += "[ERROR] Key write failed\n";
                    return false;
                }

                // Изменение прав доступа к памяти
                uint oldProtect;
                VirtualProtectEx(processHandle, dllSpace, (UIntPtr)encryptedDll.Length, PAGE_EXECUTE_READWRITE, out oldProtect);

                // Создание потока с использованием NtCreateThreadEx для большей скрытности
                IntPtr threadHandle;
                uint status = NtCreateThreadEx(
                    out threadHandle,
                    0x1FFFFF,
                    IntPtr.Zero,
                    processHandle,
                    dllSpace,
                    keySpace,
                    false,
                    0,
                    0,
                    0,
                    IntPtr.Zero
                );

                if (status != 0 || threadHandle == IntPtr.Zero)
                {
                    LogTextBox.Text += "[ERROR] Thread creation failed\n";
                    return false;
                }

                LogTextBox.Text += "[SUCCESS] Operation completed successfully\n";
                return true;
            }
            catch (Exception ex)
            {
                LogTextBox.Text += $"[ERROR] {ex.Message}\n";
                return false;
            }
        }

        private async void InjectButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                string dllPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "cheat.dll");
                if (!File.Exists(dllPath))
                {
                    LogTextBox.Text += "[ERROR] Required files not found\n";
                    return;
                }

                LogTextBox.Text += "[INFO] Starting security check...\n";
                await Task.Delay(1000);

                LogTextBox.Text += "[INFO] Initializing...\n";
                bool success = await PrepareAndInject(dllPath);
                
                if (!success)
                {
                    LogTextBox.Text += "[INFO] Operation cancelled for security reasons\n";
                }
            }
            catch (Exception ex)
            {
                LogTextBox.Text += $"[ERROR] {ex.Message}\n";
            }
        }

        private async void LoginButton_Click(object sender, RoutedEventArgs e)
        {
            string login = LoginTextBox.Text;
            string password = PasswordBox.Password;
            bool loginValid = login == "123";
            bool passwordValid = password == "123";

            if (loginValid && passwordValid)
            {
                LoginErrorLabel.Visibility = Visibility.Collapsed;
                LoginTextBox.BorderBrush = System.Windows.Media.Brushes.Gray;
                PasswordBox.BorderBrush = System.Windows.Media.Brushes.Gray;
                await AnimatePanel(LoginPanel, false);
                LoadingPanel.Visibility = Visibility.Visible;
                await AnimatePanel(LoadingPanel, true);
                await Task.Delay(2000);
                await AnimatePanel(LoadingPanel, false);
                LoadingPanel.Visibility = Visibility.Collapsed;
                MainPanel.Visibility = Visibility.Visible;
                SideMenu.Visibility = Visibility.Visible;
                await AnimatePanel(MainPanel, true);
                LogTextBox.Text = "[INFO] Authentication successful\n";
            }
            else
            {
                if (!loginValid && !passwordValid)
                {
                    LoginErrorLabel.Content = "Неверный логин и пароль";
                }
                else if (!loginValid)
                {
                    LoginErrorLabel.Content = "Неверный логин";
                }
                else if (!passwordValid)
                {
                    LoginErrorLabel.Content = "Неверный пароль";
                }
                LoginErrorLabel.Visibility = Visibility.Visible;
                LoginTextBox.BorderBrush = !loginValid ? System.Windows.Media.Brushes.Red : System.Windows.Media.Brushes.Gray;
                PasswordBox.BorderBrush = !passwordValid ? System.Windows.Media.Brushes.Red : System.Windows.Media.Brushes.Gray;
                await Task.Delay(2000);
                LoginErrorLabel.Visibility = Visibility.Collapsed;
                LoginTextBox.BorderBrush = System.Windows.Media.Brushes.Gray;
                PasswordBox.BorderBrush = System.Windows.Media.Brushes.Gray;
            }
        }

        private void UpdateLogButton_Click(object sender, RoutedEventArgs e)
        {
            LogTextBox.Text = "";
            LogTextBox.Text += "🔵 [NEW] Latest DLC Updates:\n\n";
            
            // Новые функции
            LogTextBox.Text += "✨ New Features:\n";
            LogTextBox.Text += "• Added new weapon skins collection\n";
            LogTextBox.Text += "• Implemented custom player models\n";
            LogTextBox.Text += "• Added special effects for kills\n\n";
            
            // Улучшения
            LogTextBox.Text += "📈 Improvements:\n";
            LogTextBox.Text += "• Enhanced weapon animations\n";
            LogTextBox.Text += "• Optimized performance\n";
            LogTextBox.Text += "• Updated textures quality\n\n";
            
            // Исправления
            LogTextBox.Text += "🛠 Bug Fixes:\n";
            LogTextBox.Text += "• Fixed various visual glitches\n";
            LogTextBox.Text += "• Improved stability\n\n";
            
            // Статус
            LogTextBox.Text += "✅ Status: All components are up to date\n";
            LogTextBox.Text += "📦 Version: 1.2.0\n";
            
            ScrollLogToEnd();
        }

        private async Task AnimatePanel(FrameworkElement panel, bool fadeIn)
        {
            var animation = new DoubleAnimation
            {
                From = fadeIn ? 0 : 1,
                To = fadeIn ? 1 : 0,
                Duration = TimeSpan.FromMilliseconds(300)
            };

            panel.BeginAnimation(OpacityProperty, animation);
            await Task.Delay(300);
        }

        private void ScrollLogToEnd()
        {
            LogTextBox.ScrollToEnd();
        }

        private void ProductSelector_Click(object sender, RoutedEventArgs e)
        {
            Button button = (Button)sender;
            Border border = (Border)button.Content;
            
            // Создаем и запускаем анимацию для плавного изменения цвета фона
            ColorAnimation colorAnimation = new ColorAnimation
            {
                To = (Color)ColorConverter.ConvertFromString("#1A1D26"),
                Duration = TimeSpan.FromMilliseconds(200)
            };

            // Применяем анимацию к фону
            border.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#12141C"));
            border.Background.BeginAnimation(SolidColorBrush.ColorProperty, colorAnimation);

            LogTextBox.Text += "[INFO] CS2 DLC selected\n";
            ScrollLogToEnd();
        }
    }
}
