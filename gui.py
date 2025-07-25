import flet as ft
import json
import asyncio
import threading
from main import StarBot, load_config
from datetime import datetime

class AutoStarsGUI:
    def __init__(self):
        self.config = None
        self.bot = None
        self.bot_thread = None
        self.is_running = False
        self.themes = {
            "🌌 Cyber Dark": {
                "primary": ft.Colors.CYAN_400,
                "secondary": ft.Colors.GREY_800,
                "background": ft.Colors.BLACK,
                "surface": ft.Colors.GREY_900,
                "accent": ft.Colors.BLUE_400
            },
            "🔮 Neon Purple": {
                "primary": ft.Colors.PURPLE_400,
                "secondary": ft.Colors.GREY_800,
                "background": ft.Colors.GREY_900,
                "surface": ft.Colors.GREY_800,
                "accent": ft.Colors.DEEP_PURPLE_300
            },
            "⚡ Electric Blue": {
                "primary": ft.Colors.LIGHT_BLUE_400,
                "secondary": ft.Colors.GREY_800,
                "background": ft.Colors.BLUE_GREY_900,
                "surface": ft.Colors.BLUE_GREY_800,
                "accent": ft.Colors.CYAN_300
            },
            "🌊 Deep Ocean": {
                "primary": ft.Colors.TEAL_400,
                "secondary": ft.Colors.GREY_800,
                "background": ft.Colors.BLUE_GREY_900,
                "surface": ft.Colors.BLUE_GREY_800,
                "accent": ft.Colors.TEAL_300
            },
            "🔥 Matrix Green": {
                "primary": ft.Colors.GREEN_400,
                "secondary": ft.Colors.GREY_800,
                "background": ft.Colors.BLACK,
                "surface": ft.Colors.GREY_900,
                "accent": ft.Colors.LIGHT_GREEN_300
            },
            "🌙 Midnight Dark": {
                "primary": ft.Colors.BLUE_400,
                "secondary": ft.Colors.GREY_800,
                "background": ft.Colors.GREY_900,
                "surface": ft.Colors.GREY_800,
                "accent": ft.Colors.INDIGO_300
            },
            "🚀 Space Gray": {
                "primary": ft.Colors.BLUE_GREY_400,
                "secondary": ft.Colors.GREY_800,
                "background": ft.Colors.BLUE_GREY_900,
                "surface": ft.Colors.BLUE_GREY_800,
                "accent": ft.Colors.LIGHT_BLUE_300
            },
            "💎 Diamond Blue": {
                "primary": ft.Colors.INDIGO_400,
                "secondary": ft.Colors.GREY_800,
                "background": ft.Colors.INDIGO_900,
                "surface": ft.Colors.INDIGO_800,
                "accent": ft.Colors.BLUE_300
            },
            "🌟 Amber Glow": {
                "primary": ft.Colors.AMBER_400,
                "secondary": ft.Colors.GREY_800,
                "background": ft.Colors.BROWN_900,
                "surface": ft.Colors.BROWN_800,
                "accent": ft.Colors.ORANGE_300
            },
            "🎯 Red Alert": {
                "primary": ft.Colors.RED_400,
                "secondary": ft.Colors.GREY_800,
                "background": ft.Colors.RED_900,
                "surface": ft.Colors.RED_800,
                "accent": ft.Colors.PINK_300
            }
        }
        self.current_theme = "🌌 Cyber Dark"

    def load_config_file(self):
        try:
            self.config = load_config()
            return True
        except:
            return False

    def save_config(self):
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False

    def show_message(self, page, text):
        page.snack_bar = ft.SnackBar(
            ft.Text(text, color=ft.Colors.WHITE),
            bgcolor=self.themes[self.current_theme]["primary"]
        )
        page.snack_bar.open = True
        page.update()

    def apply_theme(self, page, theme_name):
        theme = self.themes[theme_name]
        page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=theme["primary"],
                secondary=theme["secondary"],
                background=theme["background"],
                surface=theme["surface"],
                on_primary=ft.Colors.WHITE,
                on_secondary=ft.Colors.WHITE,
                on_background=ft.Colors.WHITE,
                on_surface=ft.Colors.WHITE,
            )
        )
        page.bgcolor = theme["background"]
        page.update()

    def create_main_tab(self, page):
        theme = self.themes[self.current_theme]
        status_text = ft.Text("СИСТЕМА ОСТАНОВЛЕНА", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_400)
        
        def start_bot(e):
            if not self.is_running:
                if self.load_config_file():
                    self.bot = StarBot(self.config)
                    self.bot_thread = threading.Thread(target=lambda: asyncio.run(self.bot.start_bot()))
                    self.bot_thread.daemon = True
                    self.bot_thread.start()
                    self.is_running = True
                    status_text.value = "СИСТЕМА АКТИВНА"
                    status_text.color = ft.Colors.GREEN_400
                    start_btn.content.disabled = True
                    stop_btn.content.disabled = False
                    page.update()
                else:
                    self.show_message(page, "⚠️ ОШИБКА ЗАГРУЗКИ КОНФИГУРАЦИИ")

        def stop_bot(e):
            if self.is_running:
                self.is_running = False
                if self.bot_thread and self.bot_thread.is_alive():
                    # Остановка потока бота
                    pass
                status_text.value = "СИСТЕМА ОСТАНОВЛЕНА"
                status_text.color = ft.Colors.RED_400
                start_btn.content.disabled = False
                stop_btn.content.disabled = True
                page.update()

        start_btn = ft.Container(
            content=ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.ROCKET_LAUNCH, color=ft.Colors.WHITE),
                    ft.Text("ЗАПУСК СИСТЕМЫ", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
                ], tight=True),
                on_click=start_bot,
                bgcolor=theme["primary"],
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15))
            ),
            border_radius=15,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=theme["primary"],
                offset=ft.Offset(0, 0),
                blur_style=ft.ShadowBlurStyle.OUTER,
            )
        )

        stop_btn = ft.Container(
            content=ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.POWER_SETTINGS_NEW, color=ft.Colors.WHITE),
                    ft.Text("ОСТАНОВКА", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
                ], tight=True),
                on_click=stop_bot,
                bgcolor=theme["accent"],
                disabled=True,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15))
            ),
            border_radius=15
        )

        stats_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ANALYTICS, color=theme["primary"], size=24),
                    ft.Text("СТАТИСТИКА СИСТЕМЫ", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                ]),
                ft.Divider(color=theme["primary"], height=1),
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.SHOPPING_CART, color=theme["accent"], size=30),
                            ft.Text("ЗАКАЗОВ", size=12, color=ft.Colors.WHITE70),
                            ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color=theme["primary"])
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        expand=1
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.STAR, color=theme["accent"], size=30),
                            ft.Text("ЗВЁЗД", size=12, color=ft.Colors.WHITE70),
                            ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color=theme["accent"])
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        expand=1
                    )
                ])
            ]),
            padding=20,
            bgcolor=theme["surface"],
            border_radius=15,
            border=ft.border.all(1, theme["primary"]),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=5,
                color=theme["primary"],
                offset=ft.Offset(0, 2),
                blur_style=ft.ShadowBlurStyle.OUTER,
            )
        )

        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.AUTO_AWESOME, color=theme["primary"], size=32),
                        ft.Text("AUTOSTARS CONTROL MATRIX", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(color=theme["primary"], height=2),
                    ft.Container(height=5),
                    ft.Container(
                        content=status_text,
                        alignment=ft.alignment.center
                    ),
                    ft.Container(height=10),
                    ft.Row([start_btn, stop_btn], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=20),
                    stats_card
                ]),
                padding=25,
                bgcolor=theme["surface"],
                border_radius=20,
                margin=15,
                border=ft.border.all(2, theme["primary"]),
                shadow=ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=15,
                    color=theme["primary"],
                    offset=ft.Offset(0, 5),
                    blur_style=ft.ShadowBlurStyle.OUTER,
                )
            )
        ])

    def create_autoresponder_tab(self, page):
        theme = self.themes[self.current_theme]
        
        payment_msg = ft.TextField(
            label="💰 СООБЩЕНИЕ ПРИ ОПЛАТЕ",
            value="Спасибо за оплату, {username}! Ваш заказ {order_id} на {product_name} обрабатывается.",
            multiline=True,
            max_lines=3,
            border_color=theme["primary"],
            prefix_icon=ft.Icons.PAYMENT
        )
        
        review_request = ft.TextField(
            label="⭐ ПРОСЬБА ОСТАВИТЬ ОТЗЫВ",
            value="Привет, {username}! Пожалуйста, оставьте отзыв о покупке {product_name}. Это поможет нам стать лучше!",
            multiline=True,
            max_lines=3,
            border_color=theme["primary"],
            prefix_icon=ft.Icons.RATE_REVIEW
        )
        
        review_response = ft.TextField(
            label="💬 ОТВЕТ НА ОТЗЫВ",
            value="Спасибо за отзыв, {username}! Рады, что вы довольны покупкой {product_name}.",
            multiline=True,
            max_lines=3,
            border_color=theme["primary"],
            prefix_icon=ft.Icons.REPLY
        )
        
        ai_enabled = ft.Switch(
            label="🤖 ВКЛЮЧИТЬ НЕЙРОСЕТЬ",
            value=False,
            active_color=theme["primary"]
        )
        
        ai_provider = ft.Dropdown(
            label="🧠 ПРОВАЙДЕР ИИ",
            options=[
                ft.dropdown.Option("openai", "OpenAI GPT"),
                ft.dropdown.Option("anthropic", "Claude"),
                ft.dropdown.Option("google", "Gemini")
            ],
            value="openai",
            border_color=theme["primary"]
        )
        
        ai_key = ft.TextField(
            label="🔑 API КЛЮЧ ИИ",
            password=True,
            border_color=theme["primary"],
            prefix_icon=ft.Icons.VPN_KEY
        )
        
        ai_prompt = ft.TextField(
            label="📝 ПРОМПТ ДЛЯ ИИ",
            value="Ты - помощник продавца на FunPay. Отвечай вежливо и по теме. Используй данные: username={username}, product_name={product_name}, order_id={order_id}",
            multiline=True,
            max_lines=4,
            border_color=theme["primary"],
            prefix_icon=ft.Icons.PSYCHOLOGY
        )

        def save_autoresponder(e):
            self.show_message(page, "✅ АВТООТВЕТЧИК СОХРАНЁН")

        save_btn = ft.Container(
            content=ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.SAVE, color=ft.Colors.WHITE),
                    ft.Text("СОХРАНИТЬ НАСТРОЙКИ", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
                ], tight=True),
                on_click=save_autoresponder,
                bgcolor=theme["primary"],
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15))
            ),
            border_radius=15,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=theme["primary"],
                offset=ft.Offset(0, 0),
                blur_style=ft.ShadowBlurStyle.OUTER,
            )
        )

        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.AUTO_MODE, color=theme["primary"], size=28),
                        ft.Text("АВТООТВЕТЧИК", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                    ]),
                    ft.Divider(color=theme["primary"], height=2),
                    ft.Text("📋 ДОСТУПНЫЕ ПЕРЕМЕННЫЕ: {username}, {product_name}, {order_id}, {price}", 
                           color=ft.Colors.WHITE70, size=12),
                    payment_msg,
                    review_request,
                    review_response,
                    ft.Container(height=20),
                    ai_enabled,
                    ai_provider,
                    ai_key,
                    ai_prompt,
                    ft.Container(height=20),
                    save_btn
                ]),
                padding=25,
                bgcolor=theme["surface"],
                border_radius=20,
                margin=15,
                border=ft.border.all(2, theme["primary"]),
                shadow=ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=15,
                    color=theme["primary"],
                    offset=ft.Offset(0, 5),
                    blur_style=ft.ShadowBlurStyle.OUTER,
                )
            )
        ])

    def create_about_tab(self, page):
        theme = self.themes[self.current_theme]
        
        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.INFO, color=theme["primary"], size=28),
                        ft.Text("О РАЗРАБОТЧИКЕ", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                    ]),
                    ft.Divider(color=theme["primary"], height=2),
                    ft.Container(
                        content=ft.Image(
                            src="photo.png",
                            width=150,
                            height=150,
                            border_radius=75,
                            fit=ft.ImageFit.COVER
                        ),
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(bottom=5)
                    ),
                    ft.Row([
                        ft.Text("Red", size=18, weight=ft.FontWeight.BOLD, color=theme["primary"]),
                        ft.Text("White", size=18, weight=ft.FontWeight.BOLD, color=theme["primary"]),
                        ft.Text(" Project", size=18, weight=ft.FontWeight.BOLD, color=theme["primary"])
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=0),
                    ft.Container(height=20),
                    ft.Row([
                        ft.Icon(ft.Icons.PERSON, color=theme["accent"], size=20),
                        ft.Container(
                            content=ft.Row([
                                ft.Text("РАЗРАБОТЧИК: ", color=ft.Colors.WHITE, size=16),
                                ft.TextButton(
                                    "@ruvampir",
                                    on_click=lambda _: page.launch_url("https://t.me/ruvampir"),
                                    style=ft.ButtonStyle(color=theme["primary"], padding=ft.padding.all(0))
                                )
                            ], spacing=2)
                        )
                    ]),
                    ft.Row([
                        ft.Icon(ft.Icons.TELEGRAM, color=theme["accent"], size=20),
                        ft.Container(
                            content=ft.Row([
                                ft.Text("КАНАЛ: ", color=ft.Colors.WHITE, size=16),
                                ft.TextButton(
                                    "@AutoZelenka",
                                    on_click=lambda _: page.launch_url("https://t.me/AutoZelenka"),
                                    style=ft.ButtonStyle(color=theme["primary"], padding=ft.padding.all(0))
                                )
                            ], spacing=2)
                        )
                    ]),
                    ft.Container(height=30),
                    ft.Container(
                        content=ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.TELEGRAM, color=ft.Colors.WHITE),
                                ft.Text("ПОДПИСАТЬСЯ НА КАНАЛ", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
                            ], tight=True),
                            on_click=lambda _: page.launch_url("https://t.me/AutoZelenka"),
                            bgcolor=theme["primary"],
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15))
                        ),
                        border_radius=15,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=10,
                            color=theme["primary"],
                            offset=ft.Offset(0, 0),
                            blur_style=ft.ShadowBlurStyle.OUTER,
                        )
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=25,
                bgcolor=theme["surface"],
                border_radius=20,
                margin=15,
                border=ft.border.all(2, theme["primary"]),
                shadow=ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=15,
                    color=theme["primary"],
                    offset=ft.Offset(0, 5),
                    blur_style=ft.ShadowBlurStyle.OUTER,
                )
            )
        ])

    def create_settings_tab(self, page):
        if not self.load_config_file():
            return ft.Text("⚠️ ОШИБКА ЗАГРУЗКИ КОНФИГУРАЦИИ", color=ft.Colors.RED)

        theme = self.themes[self.current_theme]
        
        api_token = ft.TextField(
            label="🔑 API TOKEN",
            value=self.config["API"]["token"],
            password=True,
            border_color=theme["primary"],
            focused_border_color=theme["accent"],
            prefix_icon=ft.Icons.VPN_KEY,
            border_radius=10
        )
        
        bot_token = ft.TextField(
            label="🤖 BOT TOKEN",
            value=self.config["BOT"]["bot_token"],
            password=True,
            border_color=theme["primary"],
            focused_border_color=theme["accent"],
            prefix_icon=ft.Icons.SMART_TOY,
            border_radius=10
        )
        
        golden_key = ft.TextField(
            label="🗝️ GOLDEN KEY",
            value=self.config["FUNPAY"]["golden_key"],
            password=True,
            border_color=theme["primary"],
            focused_border_color=theme["accent"],
            prefix_icon=ft.Icons.KEY,
            border_radius=10
        )
        
        bot_enabled = ft.Switch(
            label="📡 TELEGRAM BOT",
            value=bool(self.config["BOT"]["enabled"]),
            active_color=theme["primary"]
        )
        
        check_interval = ft.TextField(
            label="⏱️ ИНТЕРВАЛ ПРОВЕРКИ (СЕК)",
            value=str(self.config["SETTINGS"]["order_check_interval"]),
            border_color=theme["primary"],
            focused_border_color=theme["accent"],
            prefix_icon=ft.Icons.TIMER,
            border_radius=10
        )

        def save_settings(e):
            self.config["API"]["token"] = api_token.value
            self.config["BOT"]["bot_token"] = bot_token.value
            self.config["FUNPAY"]["golden_key"] = golden_key.value
            self.config["BOT"]["enabled"] = 1 if bot_enabled.value else 0
            self.config["SETTINGS"]["order_check_interval"] = int(check_interval.value)
            
            if self.save_config():
                self.show_message(page, "✅ КОНФИГУРАЦИЯ СОХРАНЕНА")
            else:
                self.show_message(page, "❌ ОШИБКА СОХРАНЕНИЯ")

        save_btn = ft.Container(
            content=ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.SAVE, color=ft.Colors.WHITE),
                    ft.Text("СОХРАНИТЬ КОНФИГУРАЦИЮ", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
                ], tight=True),
                on_click=save_settings,
                bgcolor=theme["primary"],
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15))
            ),
            border_radius=15,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=theme["primary"],
                offset=ft.Offset(0, 0),
                blur_style=ft.ShadowBlurStyle.OUTER,
            )
        )

        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.SETTINGS, color=theme["primary"], size=28),
                        ft.Text("СИСТЕМНЫЕ НАСТРОЙКИ", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                    ]),
                    ft.Divider(color=theme["primary"], height=2),
                    api_token,
                    bot_token,
                    golden_key,
                    bot_enabled,
                    check_interval,
                    ft.Container(height=20),
                    save_btn
                ]),
                padding=25,
                bgcolor=theme["surface"],
                border_radius=20,
                margin=15,
                border=ft.border.all(2, theme["primary"]),
                shadow=ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=15,
                    color=theme["primary"],
                    offset=ft.Offset(0, 5),
                    blur_style=ft.ShadowBlurStyle.OUTER,
                )
            )
        ])

    def create_history_tab(self, page):
        theme = self.themes[self.current_theme]
        try:
            with open("db.json", "r", encoding="utf-8") as f:
                db = json.load(f)
            
            history_items = []
            for user_id, user_data in db.items():
                if "payment_history" in user_data:
                    for payment in user_data["payment_history"]:
                        history_items.append(
                            ft.Container(
                                content=ft.ListTile(
                                    leading=ft.Icon(ft.Icons.STAR, color=theme["accent"], size=24),
                                    title=ft.Text(f"🎯 {payment.get('order_number', 'N/A')}", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                                    subtitle=ft.Text(f"👤 @{payment.get('login', 'N/A')} • ⭐ {payment.get('original_amount', 0)} звёзд", color=ft.Colors.WHITE70),
                                    trailing=ft.Text(payment.get('date', 'N/A'), color=theme["primary"])
                                ),
                                bgcolor=theme["secondary"],
                                border_radius=10,
                                margin=ft.margin.only(bottom=5),
                                border=ft.border.all(1, theme["primary"])
                            )
                        )
        except:
            history_items = [ft.Container(
                content=ft.Text("📭 ИСТОРИЯ ОПЕРАЦИЙ ПУСТА", color=ft.Colors.WHITE70, size=16),
                alignment=ft.alignment.center,
                padding=20
            )]

        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.HISTORY, color=theme["primary"], size=28),
                        ft.Text("ЖУРНАЛ ОПЕРАЦИЙ", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                    ]),
                    ft.Divider(color=theme["primary"], height=2),
                    ft.Container(
                        content=ft.ListView(history_items, height=400),
                        border=ft.border.all(2, theme["primary"]),
                        border_radius=15,
                        bgcolor=theme["background"]
                    )
                ]),
                padding=25,
                bgcolor=theme["surface"],
                border_radius=20,
                margin=15,
                border=ft.border.all(2, theme["primary"]),
                shadow=ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=15,
                    color=theme["primary"],
                    offset=ft.Offset(0, 5),
                    blur_style=ft.ShadowBlurStyle.OUTER,
                )
            )
        ])

    def create_themes_tab(self, page):
        current_theme = self.themes[self.current_theme]
        
        def change_theme(theme_name):
            def handler(e):
                self.current_theme = theme_name
                self.apply_theme(page, theme_name)
                self.refresh_tabs(page, self.tabs)
                self.show_message(page, f"🎨 ТЕМА ИЗМЕНЕНА: {theme_name}")
            return handler

        theme_buttons = []
        for theme_name, theme_colors in self.themes.items():
            is_current = theme_name == self.current_theme
            theme_buttons.append(
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            width=120,
                            height=80,
                            bgcolor=theme_colors["primary"],
                            border_radius=15,
                            border=ft.border.all(3, theme_colors["accent"]) if is_current else ft.border.all(1, theme_colors["secondary"]),
                            shadow=ft.BoxShadow(
                                spread_radius=1,
                                blur_radius=10,
                                color=theme_colors["primary"],
                                offset=ft.Offset(0, 0),
                                blur_style=ft.ShadowBlurStyle.OUTER,
                            ) if is_current else None
                        ),
                        ft.Text(theme_name, size=12, text_align=ft.TextAlign.CENTER, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD if is_current else ft.FontWeight.NORMAL),
                        ft.Container(
                            content=ft.ElevatedButton(
                                "ПРИМЕНИТЬ",
                                on_click=change_theme(theme_name),
                                bgcolor=theme_colors["primary"],
                                color=ft.Colors.WHITE,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                            ),
                            shadow=ft.BoxShadow(
                                spread_radius=1,
                                blur_radius=5,
                                color=theme_colors["primary"],
                                offset=ft.Offset(0, 2),
                                blur_style=ft.ShadowBlurStyle.OUTER,
                            )
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=15,
                    margin=10,
                    bgcolor=theme_colors["surface"],
                    border_radius=15,
                    width=150,
                    border=ft.border.all(2, theme_colors["primary"])
                )
            )

        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.PALETTE, color=current_theme["primary"], size=28),
                        ft.Text("ВИЗУАЛЬНЫЕ ТЕМЫ", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                    ]),
                    ft.Divider(color=current_theme["primary"], height=2),
                    ft.Row(
                        theme_buttons[:5],
                        alignment=ft.MainAxisAlignment.CENTER,
                        wrap=True
                    ),
                    ft.Row(
                        theme_buttons[5:],
                        alignment=ft.MainAxisAlignment.CENTER,
                        wrap=True
                    )
                ]),
                padding=25,
                bgcolor=current_theme["surface"],
                border_radius=20,
                margin=15,
                border=ft.border.all(2, current_theme["primary"]),
                shadow=ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=15,
                    color=current_theme["primary"],
                    offset=ft.Offset(0, 5),
                    blur_style=ft.ShadowBlurStyle.OUTER,
                )
            )
        ])

    def refresh_tabs(self, page, tabs):
        tabs.tabs[0].content = self.create_main_tab(page)
        tabs.tabs[1].content = self.create_autoresponder_tab(page)
        tabs.tabs[2].content = self.create_settings_tab(page)
        tabs.tabs[3].content = self.create_history_tab(page)
        tabs.tabs[4].content = self.create_themes_tab(page)
        tabs.tabs[5].content = self.create_about_tab(page)
        page.update()

    def main(self, page: ft.Page):
        page.title = "🌟 AutoStars - Quantum Control System"
        page.window_width = 1000
        page.window_height = 750
        page.window_resizable = False
        
        self.apply_theme(page, self.current_theme)

        tabs = ft.Tabs(
            selected_index=0,
            indicator_color=self.themes[self.current_theme]["primary"],
            label_color=ft.Colors.WHITE,
            unselected_label_color=ft.Colors.WHITE70,
            tabs=[
                ft.Tab(text="🏠 ГЛАВНАЯ", icon=ft.Icons.DASHBOARD, content=self.create_main_tab(page)),
                ft.Tab(text="🤖 АВТООТВЕТЧИК", icon=ft.Icons.AUTO_MODE, content=self.create_autoresponder_tab(page)),
                ft.Tab(text="⚙️ НАСТРОЙКИ", icon=ft.Icons.SETTINGS, content=self.create_settings_tab(page)),
                ft.Tab(text="📊 ИСТОРИЯ", icon=ft.Icons.ANALYTICS, content=self.create_history_tab(page)),
                ft.Tab(text="🎨 ТЕМЫ", icon=ft.Icons.PALETTE, content=self.create_themes_tab(page)),
                ft.Tab(text="ℹ️ О НАС", icon=ft.Icons.INFO, content=self.create_about_tab(page))
            ]
        )
        
        self.tabs = tabs
        page.add(tabs)

def main():
    app = AutoStarsGUI()
    ft.app(target=app.main)

if __name__ == "__main__":
    main()