using System;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;
using Newtonsoft.Json;

namespace WpfApp2
{
    public partial class MainWindow : Window
    {
        private bool isRunning = false;
        private AutoStarsBot bot;
        private Config config;

        public MainWindow()
        {
            InitializeComponent();
            LoadConfiguration();
            
            // Fade-in animation
            this.Opacity = 0;
            var fadeIn = new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(800));
            this.BeginAnimation(Window.OpacityProperty, fadeIn);
        }

        private void LoadConfiguration()
        {
            try
            {
                if (File.Exists("config.json"))
                {
                    string json = File.ReadAllText("config.json");
                    config = JsonConvert.DeserializeObject<Config>(json);
                    
                    // Load values to UI
                    ApiTokenBox.Text = config.API.token;
                    BotTokenBox.Text = config.BOT.bot_token;
                    GoldenKeyBox.Text = config.FUNPAY.golden_key;
                    IntervalBox.Text = config.SETTINGS.order_check_interval.ToString();
                }
                else
                {
                    // Create default config
                    config = new Config
                    {
                        API = new ApiConfig { token = "", url = "http://docs.lunovr.ru/api/buyStars" },
                        BOT = new BotConfig { enabled = 1, bot_token = "" },
                        FUNPAY = new FunPayConfig { golden_key = "" },
                        SETTINGS = new SettingsConfig { order_check_interval = 10, db_path = "db.json" }
                    };
                }
            }
            catch (Exception ex)
            {
                ShowMessage("Ошибка загрузки конфигурации: " + ex.Message, true);
            }
        }

        private void SaveConfiguration()
        {
            try
            {
                config.API.token = ApiTokenBox.Text;
                config.BOT.bot_token = BotTokenBox.Text;
                config.FUNPAY.golden_key = GoldenKeyBox.Text;
                config.SETTINGS.order_check_interval = int.Parse(IntervalBox.Text);

                string json = JsonConvert.SerializeObject(config, Formatting.Indented);
                File.WriteAllText("config.json", json);
                
                ShowMessage("✅ Конфигурация сохранена", false);
            }
            catch (Exception ex)
            {
                ShowMessage("❌ Ошибка сохранения: " + ex.Message, true);
            }
        }

        private void ShowMessage(string message, bool isError)
        {
            MessageBox.Show(message, isError ? "Ошибка" : "Информация", 
                          MessageBoxButton.OK, 
                          isError ? MessageBoxImage.Error : MessageBoxImage.Information);
        }

        private void Border_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ChangedButton == MouseButton.Left)
                DragMove();
        }

        private void CloseButton_Click(object sender, RoutedEventArgs e)
        {
            // Fade-out animation before closing
            var fadeOut = new DoubleAnimation(1, 0, TimeSpan.FromMilliseconds(400));
            fadeOut.Completed += (s, args) => Application.Current.Shutdown();
            this.BeginAnimation(Window.OpacityProperty, fadeOut);
        }

        private async void StartButton_Click(object sender, RoutedEventArgs e)
        {
            if (!isRunning)
            {
                try
                {
                    if (string.IsNullOrEmpty(config.API.token) || 
                        string.IsNullOrEmpty(config.FUNPAY.golden_key))
                    {
                        ShowMessage("⚠️ Заполните все обязательные поля в настройках", true);
                        return;
                    }

                    bot = new AutoStarsBot(config);
                    await bot.StartAsync();
                    
                    isRunning = true;
                    StatusText.Text = "СИСТЕМА АКТИВНА";
                    StatusText.Foreground = new SolidColorBrush(Colors.LimeGreen);
                    StartButton.IsEnabled = false;
                    StopButton.IsEnabled = true;
                    
                    // Glow animation for status
                    var glowAnimation = new DoubleAnimation(0.5, 1.0, TimeSpan.FromMilliseconds(1000))
                    {
                        RepeatBehavior = RepeatBehavior.Forever,
                        AutoReverse = true
                    };
                    StatusText.BeginAnimation(OpacityProperty, glowAnimation);
                    
                    ShowMessage("🚀 Система успешно запущена!", false);
                }
                catch (Exception ex)
                {
                    ShowMessage("❌ Ошибка запуска: " + ex.Message, true);
                }
            }
        }

        private async void StopButton_Click(object sender, RoutedEventArgs e)
        {
            if (isRunning)
            {
                try
                {
                    await bot.StopAsync();
                    
                    isRunning = false;
                    StatusText.Text = "СИСТЕМА ОСТАНОВЛЕНА";
                    StatusText.Foreground = new SolidColorBrush(Colors.Red);
                    StartButton.IsEnabled = true;
                    StopButton.IsEnabled = false;
                    
                    // Stop glow animation
                    StatusText.BeginAnimation(OpacityProperty, null);
                    StatusText.Opacity = 1.0;
                    
                    ShowMessage("⏹ Система остановлена", false);
                }
                catch (Exception ex)
                {
                    ShowMessage("❌ Ошибка остановки: " + ex.Message, true);
                }
            }
        }

        private void SaveButton_Click(object sender, RoutedEventArgs e)
        {
            SaveConfiguration();
        }

        private void DeveloperButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                Process.Start(new ProcessStartInfo("https://t.me/ruvampir") { UseShellExecute = true });
            }
            catch (Exception ex)
            {
                ShowMessage("Ошибка открытия ссылки: " + ex.Message, true);
            }
        }

        private void ChannelButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                Process.Start(new ProcessStartInfo("https://t.me/AutoZelenka") { UseShellExecute = true });
            }
            catch (Exception ex)
            {
                ShowMessage("Ошибка открытия ссылки: " + ex.Message, true);
            }
        }

        private void SubscribeButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                Process.Start(new ProcessStartInfo("https://t.me/AutoZelenka") { UseShellExecute = true });
            }
            catch (Exception ex)
            {
                ShowMessage("Ошибка открытия ссылки: " + ex.Message, true);
            }
        }
    }

    // Configuration classes
    public class Config
    {
        public ApiConfig API { get; set; }
        public BotConfig BOT { get; set; }
        public FunPayConfig FUNPAY { get; set; }
        public SettingsConfig SETTINGS { get; set; }
    }

    public class ApiConfig
    {
        public string url { get; set; }
        public string token { get; set; }
    }

    public class BotConfig
    {
        public int enabled { get; set; }
        public string bot_token { get; set; }
    }

    public class FunPayConfig
    {
        public string golden_key { get; set; }
    }

    public class SettingsConfig
    {
        public string db_path { get; set; }
        public int order_check_interval { get; set; }
    }

    // Simplified bot class for demonstration
    public class AutoStarsBot
    {
        private Config config;
        private bool isRunning;

        public AutoStarsBot(Config config)
        {
            this.config = config;
        }

        public async Task StartAsync()
        {
            isRunning = true;
            // Simulate bot startup
            await Task.Delay(1000);
            
            // Here you would implement the actual bot logic
            // - FunPay API integration
            // - Telegram bot setup
            // - Order monitoring
            // - Star distribution
        }

        public async Task StopAsync()
        {
            isRunning = false;
            // Simulate bot shutdown
            await Task.Delay(500);
        }
    }
}