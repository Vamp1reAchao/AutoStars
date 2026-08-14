import asyncio
import json
import sqlite3
import threading
import random
import sys
from pathlib import Path

import flet as ft

from main import StarBot, validate_config

if getattr(sys, "frozen", False):
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    APP_DIR = Path(sys.executable).resolve().parent
else:
    RESOURCE_DIR = Path(__file__).resolve().parent
    APP_DIR = RESOURCE_DIR
BASE_DIR = APP_DIR


def resource_path(name: str) -> Path:
    return RESOURCE_DIR / name


def user_path(name: str) -> Path:
    return BASE_DIR / name
COLORS = ft.Colors
ICONS = ft.Icons


class AutoStarsGUI:
    def __init__(self):
        self.config = None
        self.bot = None
        self.bot_thread = None
        self.bot_loop = None
        self.is_running = False
        self.page = None
        self.action_status = None
        self.config_error = None
        self.nav_icons = []
        self.orders_text = None
        self.stars_text = None
        self.failed_text = None
        self.unknown_text = None
        self.start_button = None
        self.stop_button = None
        self.progress = None
        self.tab_view = None
        self.tabs = None
        self.tab_bar = None
        self.current_theme = "🌌 Cyber Dark"
        self.particle_stack = None
        self.particles = []
        self.particle_task = None
        self.themes = {
            "🌌 Cyber Dark": {"primary": "#67D37B", "background": "#0F1113", "surface": "#171A1D", "surface2": "#1D2125", "accent": "#A9D77A"},
            "🔮 Neon Purple": {"primary": "#B68CFF", "background": "#100E15", "surface": "#191620", "surface2": "#211C2A", "accent": "#D4B8FF"},
            "⚡ Electric Blue": {"primary": "#62B7FF", "background": "#0C1117", "surface": "#151C24", "surface2": "#1B2632", "accent": "#8BD0FF"},
            "🌊 Deep Ocean": {"primary": "#47D7C8", "background": "#091314", "surface": "#111D1E", "surface2": "#182526", "accent": "#83E8DE"},
            "🔥 Matrix Green": {"primary": "#69E07B", "background": "#0B110D", "surface": "#121A14", "surface2": "#19231B", "accent": "#A4EFAD"},
            "🌙 Midnight Dark": {"primary": "#7EA7FF", "background": "#0B0E15", "surface": "#151925", "surface2": "#1D2231", "accent": "#AFC6FF"},
            "🚀 Space Gray": {"primary": "#A9B8C9", "background": "#101317", "surface": "#181C21", "surface2": "#20262D", "accent": "#D1D9E1"},
            "💎 Diamond Blue": {"primary": "#829BFF", "background": "#0E101B", "surface": "#171A2A", "surface2": "#20243A", "accent": "#B6C3FF"},
            "🌟 Amber Glow": {"primary": "#F2B84B", "background": "#151108", "surface": "#211A0D", "surface2": "#2B2111", "accent": "#FFD27A"},
            "🎯 Red Alert": {"primary": "#FF6B6B", "background": "#150C0C", "surface": "#211313", "surface2": "#2A1919", "accent": "#FF9A9A", "nav": "#D6D6D6"},
            "🧊 Arctic Glass": {"primary": "#7FE7FF", "background": "#081117", "surface": "#101D25", "surface2": "#172A34", "accent": "#B8F3FF"},
            "⚫ Pure Black": {"primary": "#FFFFFF", "background": "#000000", "surface": "#080808", "surface2": "#111111", "accent": "#FFFFFF", "nav": "#FFFFFF"},
        }
        for theme in self.themes.values():
            theme.setdefault("nav", "#B9BEC7")

    @property
    def theme(self):
        return self.themes[self.current_theme]

    def _merge_config_defaults(self, value, defaults):
        if isinstance(defaults, dict):
            if not isinstance(value, dict):
                value = {}
            merged = {key: item for key, item in defaults.items()}
            for key, item in value.items():
                merged[key] = self._merge_config_defaults(item, defaults.get(key)) if key in defaults else item
            return merged
        return defaults if value is None else value

    def load_config_file(self, strict=True):
        path = user_path("config.json")
        example_path = resource_path("config.example.json")
        if not example_path.exists():
            example_path = user_path("config.example.json")
        try:
            if not path.exists():
                if not example_path.exists():
                    raise RuntimeError("config.json и config.example.json не найдены.")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")
            with path.open("r", encoding="utf-8") as file:
                raw = json.load(file)
            defaults = {}
            if example_path.exists():
                with example_path.open("r", encoding="utf-8") as file:
                    defaults = json.load(file)
            self.config = self._merge_config_defaults(raw, defaults)
            self.config_error = None
            try:
                validate_config(self.config)
            except Exception as exc:
                self.config_error = str(exc)
                if strict:
                    raise
            return True
        except json.JSONDecodeError as exc:
            self.config_error = f"Некорректный JSON в config.json: {exc}"
            if example_path.exists():
                try:
                    self.config = json.loads(example_path.read_text(encoding="utf-8"))
                except Exception:
                    self.config = None
            return self.config is not None
        except Exception as exc:
            self.config_error = str(exc)
            return False

    def save_config(self):
        try:
            validate_config(self.config)
            with user_path("config.json").open("w", encoding="utf-8") as file:
                json.dump(self.config, file, ensure_ascii=False, indent=2)
            return True
        except Exception as exc:
            self.config_error = str(exc)
            return False

    def show_message(self, page, text, color=None):
        if self.action_status is not None:
            self.action_status.value = text
            self.action_status.color = color or self.theme["accent"]
            self.action_status.visible = True
            self.action_status.update()
        else:
            try:
                page.show_dialog(ft.SnackBar(content=ft.Text(text, color=COLORS.WHITE), bgcolor=color or self.theme["primary"]))
            except Exception:
                page.update()


    def create_particles(self, page):
        self.particles = []
        controls = []
        palette = [self.theme["primary"], self.theme["accent"], "#FFFFFF"]
        for _ in range(22):
            size = random.choice([2, 2, 3, 3, 4, 5])
            color = random.choice(palette)
            opacity = random.choice([0.08, 0.10, 0.12, 0.15, 0.18])
            particle = ft.Container(
                width=size,
                height=size,
                bgcolor=color,
                opacity=opacity,
                border_radius=size,
                left=random.uniform(10, 1000),
                top=random.uniform(10, 700),
                animate_position=ft.Animation(random.randint(2500, 6500), ft.AnimationCurve.EASE_IN_OUT),
            )
            self.particles.append(particle)
            controls.append(particle)
        self.particle_stack = ft.Stack(controls=controls, expand=True, clip_behavior=ft.ClipBehavior.NONE)
        page.run_task(self.animate_particles)
        return self.particle_stack

    async def animate_particles(self):
        while self.page is not None:
            width = max(float(self.page.width or 1100), 760.0)
            height = max(float(self.page.height or 760), 620.0)
            for particle in self.particles:
                particle.left = random.uniform(-10, width - 5)
                particle.top = random.uniform(-10, height - 5)
            if self.particle_stack and self.page:
                self.particle_stack.update()
            await asyncio.sleep(4.0)

    def recolor_particles(self):
        if not self.particles:
            return
        palette = [self.theme["primary"], self.theme["accent"], "#FFFFFF"]
        for particle in self.particles:
            particle.bgcolor = random.choice(palette)
        if self.particle_stack:
            self.particle_stack.update()

    def update_nav_colors(self, e=None):
        if not self.nav_icons or not self.tab_bar:
            return
        selected = self.tabs.selected_index if self.tabs else 0
        for index, icon in enumerate(self.nav_icons):
            icon.color = self.theme["primary"] if index == selected else self.theme.get("nav", "#B9BEC7")
        self.tab_bar.update()

    def apply_theme(self, page, theme_name):
        self.current_theme = theme_name
        theme = self.themes[theme_name]
        page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=theme["primary"],
                secondary=theme["accent"],
                surface=theme["surface"],
                on_primary=COLORS.WHITE,
                on_secondary=COLORS.BLACK,
                on_surface=COLORS.WHITE,
            ),
            scaffold_bgcolor=theme["background"],
            canvas_color=theme["background"],
            card_bgcolor=theme["surface"],
        )
        page.bgcolor = theme["background"]
        if self.tab_bar:
            self.tab_bar.label_color = theme["primary"]
            self.tab_bar.unselected_label_color = theme.get("nav", "#B9BEC7")
            self.tab_bar.indicator_color = theme["primary"]
            self.tab_bar.divider_color = COLORS.TRANSPARENT
            self.update_nav_colors()
        self.recolor_particles()

    def db_path(self):
        if not self.config:
            return BASE_DIR / "autostars.db"
        configured = Path(self.config["SETTINGS"]["db_path"])
        if configured.suffix.lower() == ".json":
            configured = configured.with_suffix(".db")
        return BASE_DIR / configured

    def read_stats(self):
        path = self.db_path()
        if not path.exists():
            return {"orders": 0, "stars": 0, "failed": 0, "unknown": 0}
        try:
            with sqlite3.connect(path) as connection:
                orders = connection.execute("SELECT COUNT(*) FROM orders WHERE status='completed'").fetchone()[0]
                stars = connection.execute("SELECT COALESCE(SUM(stars),0) FROM transactions").fetchone()[0]
                failed = connection.execute("SELECT COUNT(*) FROM orders WHERE status='failed'").fetchone()[0]
                unknown = connection.execute("SELECT COUNT(*) FROM orders WHERE status='unknown'").fetchone()[0]
                return {"orders": orders, "stars": stars, "failed": failed, "unknown": unknown}
        except sqlite3.Error:
            return {"orders": 0, "stars": 0, "failed": 0, "unknown": 0}

    def update_stats(self, e=None):
        if not self.orders_text:
            return
        stats = self.read_stats()
        self.orders_text.value = f"{stats['orders']:,}".replace(",", " ")
        self.stars_text.value = f"{stats['stars']:,}".replace(",", " ")
        self.failed_text.value = f"{stats['failed']:,}".replace(",", " ")
        self.unknown_text.value = f"{stats['unknown']:,}".replace(",", " ")
        self.page.update()

    def set_status(self, title, detail, color, running=None, loading=False):
        if self.progress:
            self.progress.visible = loading
            self.progress.color = color
        if running is True:
            self.start_button.disabled = True
            self.stop_button.disabled = False
        elif running is False:
            self.start_button.disabled = False
            self.stop_button.disabled = True
        self.page.update()

    async def start_bot_click(self, e):
        await self.start_bot(e)

    async def stop_bot_click(self, e):
        await self.stop_bot(e)

    async def recheck_unknown_click(self, e):
        await self.recheck_unknown(e)

    def update_stats_click(self, e=None):
        try:
            if not self.config:
                self.load_config_file(strict=False)
            stats = self.read_stats()
            if self.orders_text:
                self.orders_text.value = f"{stats['orders']:,}".replace(",", " ")
                self.stars_text.value = f"{stats['stars']:,}".replace(",", " ")
                self.failed_text.value = f"{stats['failed']:,}".replace(",", " ")
                self.unknown_text.value = f"{stats['unknown']:,}".replace(",", " ")
                self.page.update()
            self.show_message(self.page, "🔄 Статистика обновлена", self.theme["accent"])
        except Exception as exc:
            self.show_message(self.page, f"❌ Не удалось обновить статистику: {exc}", COLORS.RED_700)

    async def start_bot(self, e):
        if self.is_running:
            return
        if not self.load_config_file():
            error = self.config_error or "Не удалось загрузить конфигурацию."
            self.set_status("", "", COLORS.RED_400, False, False)
            self.show_message(self.page, f"❌ Ошибка config.json: {error}", COLORS.RED_700)
            return
        try:
            self.bot = StarBot(self.config)
        except Exception as exc:
            self.set_status("", "", COLORS.RED_400, False, False)
            self.show_message(self.page, f"❌ {exc}", COLORS.RED_600)
            return

        self.set_status("", "", COLORS.AMBER_400, None, True)
        self.action_status.value = "🔎 Проверяем FunPay, Telegram и TON…"
        self.action_status.color = COLORS.AMBER_400
        self.action_status.visible = True
        self.start_button.disabled = True
        self.stop_button.disabled = True
        self.page.update()

        def runner():
            try:
                self.bot_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.bot_loop)
                self.bot_loop.run_until_complete(self.bot.start_bot())
            except Exception as exc:
                self.bot.startup_error = str(exc)
                self.bot.startup_event.set()
            finally:
                self.bot_loop = None
                if not self.bot.ready:
                    self.is_running = False

        self.bot_thread = threading.Thread(target=runner, name="AutoStarsBot", daemon=True)
        self.bot_thread.start()
        await asyncio.to_thread(self.bot.startup_event.wait)

        if self.bot.ready:
            self.is_running = True
            self.set_status("", "", COLORS.GREEN_400, True, False)
            self.show_message(self.page, "✅ AutoStars запущен", COLORS.GREEN_700)
        else:
            error = self.bot.startup_error or "Неизвестная ошибка запуска."
            self.is_running = False
            self.set_status("", "", COLORS.RED_400, False, False)
            self.show_message(self.page, f"❌ {error}", COLORS.RED_700)

    async def recheck_unknown(self, e):
        if not self.config and not self.load_config_file(strict=False):
            self.show_message(self.page, f"❌ Ошибка config.json: {self.config_error or 'неизвестная ошибка'}", COLORS.RED_700)
            return
        self.show_message(self.page, "🔍 Проверяем неизвестные транзакции…", self.theme["surface2"])
        temporary_bot = False
        bot = self.bot
        try:
            if bot and self.bot_loop and self.is_running:
                account = bot._funpay_account
                if account is None:
                    raise RuntimeError("FunPay-подключение сейчас недоступно.")
                future = asyncio.run_coroutine_threadsafe(bot.recheck_unknown_orders(account, bot.settings.get("admin_telegram_id")), self.bot_loop)
                await asyncio.wrap_future(future)
            else:
                bot = StarBot(self.config)
                temporary_bot = True
                account = await bot.get_funpay_account()
                if account is None:
                    raise RuntimeError("Не удалось подключиться к FunPay для проверки неизвестных заказов.")
                await bot.recheck_unknown_orders(account, bot.settings.get("admin_telegram_id"))
            self.update_stats_click()
            self.show_message(self.page, "✅ Повторная проверка завершена.", COLORS.GREEN_700)
        except Exception as exc:
            self.show_message(self.page, f"❌ Ошибка проверки: {exc}", COLORS.RED_700)
        finally:
            if temporary_bot:
                try:
                    await bot.stop()
                except Exception:
                    pass

    async def stop_bot(self, e):
        if not self.bot or not self.bot_loop or not self.is_running:
            self.set_status("", "Система не запущена.", COLORS.RED_400, False, False)
            return
        self.set_status("", "", COLORS.AMBER_400, None, True)
        self.show_message(self.page, "⏳ Останавливаем FunPay-чекер, Telegram и автоответчик…", COLORS.AMBER_400)
        self.start_button.disabled = True
        self.stop_button.disabled = True
        self.page.update()
        future = asyncio.run_coroutine_threadsafe(self.bot.stop(), self.bot_loop)
        try:
            await asyncio.wrap_future(future)
        except Exception as exc:
            self.show_message(self.page, f"⚠️ Ошибка остановки: {exc}", COLORS.ORANGE_700)
        self.is_running = False
        self.set_status("", "", COLORS.RED_400, False, False)
        self.show_message(self.page, "⏹ AutoStars остановлен", COLORS.GREY_700)

    def card(self, content, bgcolor=None, padding=18, radius=18):
        return ft.Container(content=content, bgcolor=bgcolor or self.theme["surface"], padding=padding, border_radius=radius)

    def metric(self, icon, title, value_control, color, col):
        content = ft.Row(
            controls=[
                ft.Container(content=ft.Icon(icon, color=color, size=25), width=46, height=46, bgcolor=self.theme["surface2"], border_radius=14, alignment=ft.Alignment.CENTER),
                ft.Column(controls=[ft.Text(title, size=11, color="#99FFFFFF"), value_control], spacing=2, expand=True),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        return ft.Container(content=self.card(content, self.theme["surface"]), col=col)

    def create_main_tab(self, page):
        theme = self.theme
        self.progress = ft.ProgressRing(width=18, height=18, stroke_width=2, visible=False, color=theme["accent"])
        self.orders_text = ft.Text("0", size=25, weight=ft.FontWeight.BOLD, color=theme["primary"])
        self.stars_text = ft.Text("0", size=25, weight=ft.FontWeight.BOLD, color=theme["accent"])
        self.failed_text = ft.Text("0", size=25, weight=ft.FontWeight.BOLD, color=COLORS.ORANGE_400)
        self.unknown_text = ft.Text("0", size=25, weight=ft.FontWeight.BOLD, color=COLORS.RED_400)

        self.start_button = ft.Button(content="🚀  ЗАПУСТИТЬ СИСТЕМУ", on_click=self.start_bot_click, bgcolor=theme["primary"], color=COLORS.BLACK, height=46)
        self.stop_button = ft.Button(content="⏹  ОСТАНОВИТЬ", on_click=self.stop_bot_click, bgcolor=theme["surface2"], color=COLORS.WHITE, disabled=True, height=46)
        self.action_status = ft.Text("", size=11, color=theme["accent"], text_align=ft.TextAlign.CENTER, visible=False)

        self.update_stats()

        header = self.card(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(content=ft.Icon(ICONS.STAR, color=theme["primary"], size=28), width=46, height=46, bgcolor=theme["surface2"], border_radius=14, alignment=ft.Alignment.CENTER),
                            ft.Column(controls=[ft.Text("AUTOSTARS", size=22, weight=ft.FontWeight.BOLD, color=COLORS.WHITE), ft.Text("CONTROL CENTER", size=11, color="#99FFFFFF")], spacing=0, expand=True),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=1, color="#1AFFFFFF"),
                    ft.Row([self.start_button, self.stop_button], alignment=ft.MainAxisAlignment.CENTER, spacing=10, wrap=True),
                    ft.Row([self.progress, self.action_status], alignment=ft.MainAxisAlignment.CENTER, spacing=9),
                ], spacing=14,
            ),
            bgcolor=theme["surface"],
            padding=22,
        )

        stats = ft.ResponsiveRow(
            controls=[
                self.metric(ICONS.SHOPPING_CART, "ЗАКАЗОВ", self.orders_text, theme["primary"], {"xs": 6, "md": 3}),
                self.metric(ICONS.STAR, "ЗВЁЗД", self.stars_text, theme["accent"], {"xs": 6, "md": 3}),
                self.metric(ICONS.WARNING, "ОШИБОК", self.failed_text, COLORS.ORANGE_400, {"xs": 6, "md": 3}),
                self.metric(ICONS.ERROR, "НЕИЗВЕСТНО", self.unknown_text, COLORS.RED_400, {"xs": 6, "md": 3}),
            ],
            spacing=10,
            run_spacing=10,
        )

        quick = ft.ResponsiveRow(
            controls=[
                ft.Container(content=self.card(ft.Column([ft.Text("БЫСТРЫЙ СТАТУС", size=12, weight=ft.FontWeight.BOLD, color=theme["accent"]), ft.Text("Управление статистикой и проверка платежей, ожидающих подтверждения.", color="#B3FFFFFF", size=12), ft.Row([ft.Button(content="🔄  ОБНОВИТЬ СТАТИСТИКУ", on_click=self.update_stats_click, bgcolor=theme["surface2"], color=COLORS.WHITE), ft.Button(content="🔍  ПРОВЕРИТЬ НЕИЗВЕСТНЫЕ", on_click=self.recheck_unknown_click, bgcolor=theme["surface2"], color=COLORS.WHITE)], spacing=10, wrap=True)], spacing=10), padding=20), height=150, col={"xs": 12, "md": 7}),
                ft.Container(content=self.card(ft.Column([ft.Text("БЕЗОПАСНЫЙ ЗАПУСК", size=12, weight=ft.FontWeight.BOLD, color=theme["accent"]), ft.Row([ft.Icon(ICONS.VERIFIED_USER, color=theme["accent"], size=18), ft.Text("Проверка FunPay / Telegram / TON", color="#B3FFFFFF", size=12)], spacing=8), ft.Text("Система становится активной только после успешной проверки подключений.", color="#80FFFFFF", size=11)], spacing=9), padding=20), height=150, col={"xs": 12, "md": 5}),
            ],
            spacing=10,
            run_spacing=10,
        )

        return ft.Column(controls=[header, stats, quick], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

    def field(self, label, value, password=False, multiline=False, min_lines=None, max_lines=None, col=None):
        kwargs = dict(
            label=label,
            value=value,
            password=password,
            border=ft.InputBorder.NONE,
            filled=True,
            bgcolor=self.theme["surface2"],
            border_radius=12,
            color=COLORS.WHITE,
        )
        if multiline:
            kwargs.update(multiline=True, min_lines=min_lines, max_lines=max_lines)
        control = ft.TextField(**kwargs)
        if col is not None:
            control.col = col
        return control

    def _settings_row(self, *controls):
        responsive = []
        for control in controls:
            responsive.append(ft.Container(content=control, col={"xs": 12, "md": 6}))
        return ft.ResponsiveRow(controls=responsive, spacing=10, run_spacing=10)

    def _settings_full(self, control):
        return ft.Container(content=control, col={"xs": 12})

    def create_settings_tab(self, page):
        if not self.load_config_file(strict=False):
            return ft.Column(
                controls=[
                    ft.Text("❌ Не удалось прочитать config.json", color=COLORS.RED_400, size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(self.config_error or "Неизвестная ошибка.", color="#B3FFFFFF", selectable=True),
                ],
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )

        theme = self.theme
        config_warning = ft.Text(
            f"⚠️ Конфигурация требует проверки: {self.config_error}",
            color=COLORS.ORANGE_400,
            size=12,
        ) if self.config_error else None
        payment = self.config.get("PAYMENT", {})
        fragment = self.config.get("FRAGMENT", {})
        bot = self.config.get("BOT", {})
        funpay = self.config.get("FUNPAY", {})
        settings = self.config.get("SETTINGS", {})

        api_key = self.field("TON API KEY", payment.get("api_key", ""), True)
        mnemonic = self.field("TON MNEMONIC", " ".join(payment.get("mnemonic", [])), True)
        destination = self.field("DESTINATION ADDRESS", payment.get("destination_address", ""))
        wallet_address = self.field("TON WALLET ADDRESS", payment.get("wallet_address", ""))
        allowed_quantities = self.field("РАЗМЕРЫ ЛОТОВ STARS", ", ".join(map(str, payment.get("allowed_quantities", []))))
        toncenter = self.field("TONCENTER URL", payment.get("toncenter_url", ""))
        fragment_hash = self.field("FRAGMENT HASH (FALLBACK)", fragment.get("hash", ""), True)
        fragment_cookie = self.field("FRAGMENT COOKIE", fragment.get("cookie", ""), True)
        fragment_url = self.field("FRAGMENT URL", fragment.get("url", ""))
        fragment_device = self.field("FRAGMENT DEVICE JSON", payment.get("device", ""), multiline=True, min_lines=3, max_lines=6)
        fragment_test_username = self.field("FRAGMENT TEST USERNAME", fragment.get("test_username", ""))
        fragment_rate_limit = self.field("FRAGMENT RATE LIMIT, SEC", str(fragment.get("rate_limit_delay", 1)))
        fragment_retries = self.field("FRAGMENT RETRIES", str(fragment.get("retry_attempts", 3)))
        fragment_min_stars = self.field("MIN STARS", str(fragment.get("min_stars", 50)))
        fragment_max_stars = self.field("MAX STARS", str(fragment.get("max_stars", 10000000)))
        bot_token = self.field("BOT TOKEN", bot.get("bot_token", ""), True)
        golden_key = self.field("FUNPAY GOLDEN KEY", funpay.get("golden_key", ""), True)
        admin_id = self.field("ADMIN TELEGRAM ID", str(settings.get("admin_telegram_id") or ""))
        interval = self.field("ИНТЕРВАЛ ПРОВЕРКИ, СЕК", str(settings.get("order_check_interval", 10)))
        timeout = self.field("TIMEOUT, СЕК", str(settings.get("request_timeout", 10)))
        confirmation_attempts = self.field("ПОПЫТКИ ПОДТВЕРЖДЕНИЯ", str(payment.get("confirmation_attempts", 25)))
        confirmation_delay = self.field("ЗАДЕРЖКА ПОДТВЕРЖДЕНИЯ, СЕК", str(payment.get("confirmation_delay", 5)))
        min_balance_reserve = self.field("РЕЗЕРВ TON НА КОМИССИИ", str(payment.get("min_balance_reserve", 0.05)))
        auto_refund = ft.Switch(label="Автовозврат при однозначной ошибке", value=bool(payment.get("auto_refund", False)), active_color=theme["primary"])
        testnet = ft.Switch(label="TON TESTNET", value=bool(payment.get("is_testnet", False)), active_color=theme["primary"])
        enabled = ft.Switch(label="Telegram-бот", value=bool(bot.get("enabled", 0)), active_color=theme["primary"])

        def save_settings(e):
            try:
                mnemonic_words = mnemonic.value.split()
                if len(mnemonic_words) not in (12, 24):
                    raise ValueError("Мнемоника должна содержать 12 или 24 слова.")
                self.config["PAYMENT"]["api_key"] = api_key.value.strip()
                self.config["PAYMENT"]["mnemonic"] = mnemonic_words
                self.config["PAYMENT"]["destination_address"] = destination.value.strip()
                self.config["PAYMENT"]["wallet_address"] = wallet_address.value.strip()
                quantities = [int(value.strip()) for value in allowed_quantities.value.split(",") if value.strip()]
                if not quantities or any(value <= 0 for value in quantities) or len(set(quantities)) != len(quantities):
                    raise ValueError("Размеры лотов Stars должны быть уникальными положительными числами.")
                self.config["PAYMENT"]["allowed_quantities"] = quantities
                self.config["PAYMENT"]["toncenter_url"] = toncenter.value.strip()
                self.config["PAYMENT"]["confirmation_attempts"] = int(confirmation_attempts.value)
                self.config["PAYMENT"]["confirmation_delay"] = float(confirmation_delay.value)
                self.config["PAYMENT"]["min_balance_reserve"] = float(min_balance_reserve.value)
                self.config["PAYMENT"]["auto_refund"] = bool(auto_refund.value)
                self.config["PAYMENT"]["is_testnet"] = bool(testnet.value)
                self.config["FRAGMENT"]["hash"] = fragment_hash.value.strip()
                self.config["FRAGMENT"]["cookie"] = fragment_cookie.value.strip()
                self.config["FRAGMENT"]["url"] = fragment_url.value.strip()
                self.config["PAYMENT"]["device"] = fragment_device.value.strip()
                self.config["PAYMENT"]["payment_method"] = "ton"
                self.config["PAYMENT"]["delivery_retry_attempts"] = 3
                self.config["PAYMENT"]["delivery_retry_delay"] = 5
                self.config["FRAGMENT"]["test_username"] = fragment_test_username.value.strip()
                self.config["FRAGMENT"]["rate_limit_delay"] = float(fragment_rate_limit.value)
                self.config["FRAGMENT"]["retry_attempts"] = int(fragment_retries.value)
                self.config["FRAGMENT"]["min_stars"] = int(fragment_min_stars.value)
                self.config["FRAGMENT"]["max_stars"] = int(fragment_max_stars.value)
                self.config["BOT"]["bot_token"] = bot_token.value.strip()
                self.config["BOT"]["enabled"] = 1 if enabled.value else 0
                self.config["FUNPAY"]["golden_key"] = golden_key.value.strip()
                self.config["SETTINGS"]["order_check_interval"] = int(interval.value)
                self.config["SETTINGS"]["request_timeout"] = int(timeout.value)
                self.config["SETTINGS"]["admin_telegram_id"] = int(admin_id.value) if admin_id.value.strip() else None
                if self.save_config():
                    self.config_error = None
                    self.show_message(page, "✅ Конфигурация сохранена", COLORS.GREEN_700)
                else:
                    self.show_message(page, f"❌ Конфигурация не сохранена: {self.config_error or 'не прошла проверку'}", COLORS.RED_700)
            except (ValueError, TypeError) as exc:
                self.show_message(page, f"❌ Проверьте настройки: {exc}", COLORS.RED_700)

        def section(title, subtitle, controls):
            return self.card(
                ft.Column(
                    controls=[
                        ft.Text(title, size=17, weight=ft.FontWeight.BOLD, color=COLORS.WHITE),
                        ft.Text(subtitle, size=11, color="#80FFFFFF"),
                        ft.Column(controls=controls, spacing=10),
                    ],
                    spacing=10,
                ),
                bgcolor=theme["surface"],
                padding=20,
            )

        ton_controls = [
            self._settings_row(api_key, mnemonic),
            self._settings_row(destination, wallet_address),
            self._settings_row(allowed_quantities, toncenter),
            self._settings_row(fragment_hash, fragment_cookie),
            self._settings_full(fragment_url),
            self._settings_full(fragment_device),
            self._settings_row(fragment_test_username, fragment_rate_limit),
            self._settings_row(fragment_retries, fragment_min_stars),
            self._settings_row(fragment_max_stars, confirmation_attempts),
            self._settings_row(confirmation_delay, min_balance_reserve),
            ft.ResponsiveRow(controls=[ft.Container(content=auto_refund, col={"xs": 12, "md": 6}), ft.Container(content=testnet, col={"xs": 12, "md": 6})], spacing=10, run_spacing=10),
        ]
        service_controls = [
            self._settings_row(bot_token, golden_key),
            self._settings_row(admin_id, interval),
            self._settings_full(timeout),
            self._settings_full(enabled),
        ]

        controls = []
        if config_warning:
            controls.append(config_warning)
        controls.extend([
            section("💎 TON / FRAGMENT", "Платёжная часть. Секретные значения скрыты.", ton_controls),
            section("🤖 TELEGRAM / FUNPAY", "Данные бота, FunPay и параметры опроса заказов.", service_controls),
            ft.Row(
                controls=[
                    ft.Button(content="💾  СОХРАНИТЬ ИЗМЕНЕНИЯ", on_click=save_settings, bgcolor=theme["primary"], color=COLORS.BLACK, height=44),
                    ft.Text("После изменения платёжных данных перезапустите систему.", size=11, color="#80FFFFFF"),
                ],
                wrap=True,
                spacing=12,
            ),
        ])
        return ft.Column(controls=controls, spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

    def create_autoreply_tab(self, page):
        if not self.load_config_file(strict=False):
            return ft.Column([ft.Text("❌ Не удалось прочитать config.json", color=COLORS.RED_400), ft.Text(self.config_error or "Неизвестная ошибка.", color="#B3FFFFFF", selectable=True)], spacing=8)
        theme = self.theme
        config_warning = ft.Text(f"⚠️ Конфигурация требует проверки: {self.config_error}", color=COLORS.ORANGE_400, size=12) if self.config_error else None
        settings = self.config["AUTOREPLY"]
        enabled = ft.Switch(label="АВТООТВЕТЧИК ВКЛЮЧЁН", value=bool(int(settings.get("enabled", 0))), active_color=theme["primary"])
        delay = self.field("ЗАДЕРЖКА ПЕРЕД ОТВЕТОМ, СЕК", str(settings.get("delay", 1)), col={"xs": 12, "md": 4})
        cooldown = self.field("КУЛДАУН НА ЧАТ, СЕК", str(settings.get("cooldown", 30)), col={"xs": 12, "md": 4})
        poll_interval = self.field("ИНТЕРВАЛ ПРОВЕРКИ, СЕК", str(settings.get("poll_interval", 2)), col={"xs": 12, "md": 4})
        rules = self.field("ПРАВИЛА JSON", json.dumps(settings.get("rules", []), ensure_ascii=False, indent=2), col={"xs": 12}, multiline=True, min_lines=12, max_lines=24)
        status = ft.Text("Первое подходящее правило отправляется автоматически.", color="#99FFFFFF", size=12)

        def save_autoreply(e):
            try:
                parsed_rules = json.loads(rules.value)
                if not isinstance(parsed_rules, list):
                    raise ValueError("Правила должны быть JSON-массивом.")
                for rule in parsed_rules:
                    if not isinstance(rule, dict) or not rule.get("triggers") or not str(rule.get("response", "")).strip():
                        raise ValueError("Каждое правило должно содержать triggers и response.")
                self.config["AUTOREPLY"]["enabled"] = 1 if enabled.value else 0
                self.config["AUTOREPLY"]["delay"] = float(delay.value)
                self.config["AUTOREPLY"]["cooldown"] = int(cooldown.value)
                self.config["AUTOREPLY"]["poll_interval"] = int(poll_interval.value)
                self.config["AUTOREPLY"]["rules"] = parsed_rules
                if self.save_config():
                    status.value = "✅ Настройки сохранены. Для изменения активного автоответчика перезапустите систему."
                    status.color = COLORS.GREEN_400
                else:
                    status.value = "❌ Не удалось сохранить настройки."
                    status.color = COLORS.RED_400
                page.update()
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                status.value = f"❌ {exc}"
                status.color = COLORS.RED_400
                page.update()

        return ft.Column(
            [*([config_warning] if config_warning else []),
                ft.ResponsiveRow(
                    controls=[
                        ft.Container(content=self.card(ft.Column([ft.Text("🤖 АВТООТВЕТЧИК", size=21, weight=ft.FontWeight.BOLD, color=theme["primary"]), ft.Text("Автоматические ответы на новые сообщения FunPay без Cardinal.", color="#99FFFFFF", size=12), enabled, ft.ResponsiveRow([delay, cooldown, poll_interval], spacing=10, run_spacing=10)], spacing=12)), col={"xs": 12, "md": 5}),
                        ft.Container(content=self.card(ft.Column([ft.Text("ПРАВИЛА", size=17, weight=ft.FontWeight.BOLD, color=COLORS.WHITE), ft.Text("contains, exact, regex. Переменные: {username}, {chat_id}.", size=11, color="#80FFFFFF"), ft.Container(content=rules, expand=True), status, ft.Button(content="💾  СОХРАНИТЬ АВТООТВЕТЧИК", on_click=save_autoreply, bgcolor=theme["primary"], color=COLORS.BLACK)], spacing=10, expand=True), padding=20), col={"xs": 12, "md": 7}),
                    ],
                    spacing=12,
                    run_spacing=12,
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def create_history_tab(self, page):
        theme = self.theme
        path = self.db_path()
        items = []
        try:
            with sqlite3.connect(path) as connection:
                connection.row_factory = sqlite3.Row
                rows = connection.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT 100").fetchall()
            for row in rows:
                items.append(
                    ft.Container(
                        content=ft.ListTile(
                            leading=ft.Icon(ICONS.STAR, color=theme["accent"]),
                            title=ft.Text(f"#{row['order_id']}  •  {row['stars']} звёзд", color=COLORS.WHITE),
                            subtitle=ft.Text(f"@{row['login']}  •  {row['tx_hash']}", color="#99FFFFFF"),
                            trailing=ft.Text(str(row['created_at']), color=theme["primary"], size=10),
                        ),
                        bgcolor=theme["surface2"],
                        border_radius=12,
                    )
                )
        except sqlite3.Error:
            pass
        if not items:
            items = [ft.Container(content=ft.Column([ft.Icon(ICONS.MAIL, size=38, color="#4DFFFFFF"), ft.Text("История операций пока пуста", color="#99FFFFFF")], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=40, alignment=ft.Alignment.CENTER)]
        return ft.Column([self.card(ft.Column([ft.Text("📊 ЖУРНАЛ ОПЕРАЦИЙ", size=20, weight=ft.FontWeight.BOLD, color=COLORS.WHITE), ft.Text("Последние подтверждённые платежи.", size=11, color="#80FFFFFF"), ft.ListView(items, expand=True)], spacing=12), self.theme["surface"])], scroll=ft.ScrollMode.AUTO, expand=True)

    def create_themes_tab(self, page):
        theme = self.theme

        def choose(name):
            def handler(e):
                self.apply_theme(page, name)
                self.refresh_tabs(page)
                self.show_message(page, f"🎨 Тема {name} применена")
            return handler

        cards = []
        for name, colors in self.themes.items():
            cards.append(
                ft.Container(
                    content=ft.Column([ft.Container(width=110, height=54, bgcolor=colors["primary"], border_radius=14), ft.Text(name, size=11, text_align=ft.TextAlign.CENTER, color=COLORS.WHITE), ft.Button(content="ПРИМЕНИТЬ", on_click=choose(name), bgcolor=colors["primary"], color=COLORS.BLACK)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    bgcolor=colors["surface"],
                    padding=12,
                    border_radius=16,
                    col={"xs": 6, "sm": 4, "md": 3, "lg": 2},
                )
            )
        return ft.Column([ft.ResponsiveRow(controls=cards, spacing=10, run_spacing=10)], scroll=ft.ScrollMode.AUTO, expand=True)

    def create_about_tab(self, page):
        theme = self.theme
        return ft.Column([self.card(ft.Column([ft.Row([ft.Container(content=ft.Icon(ICONS.STAR, color=theme["primary"], size=30), width=50, height=50, bgcolor=theme["surface2"], border_radius=14, alignment=ft.Alignment.CENTER), ft.Column([ft.Text("AUTOSTARS", size=24, weight=ft.FontWeight.BOLD, color=COLORS.WHITE), ft.Text("Standalone Stars automation", size=11, color="#80FFFFFF")], spacing=0)], alignment=ft.MainAxisAlignment.CENTER), ft.Image(src="photo.png", width=120, height=120, fit=ft.BoxFit.COVER, border_radius=60), ft.Text("Автоматическая выдача Telegram Stars через FunPay, Fragment и TON.", color="#B3FFFFFF", size=14, text_align=ft.TextAlign.CENTER), ft.Row([ft.TextButton("@ruvampir", url="https://t.me/ruvampir"), ft.TextButton("@AutoZelenka", url="https://t.me/AutoZelenka")], alignment=ft.MainAxisAlignment.CENTER)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15), self.theme["surface"])], scroll=ft.ScrollMode.AUTO, expand=True)

    def retry_tab(self, builder, page, name):
        try:
            self.show_message(page, f"🔄 Повторно загружаем: {name}…", self.theme["accent"])
            replacement = self.safe_tab(builder, page, name)
            if self.tab_view and self.tabs:
                index = self.tabs.selected_index
                if 0 <= index < len(self.tab_view.controls):
                    self.tab_view.controls[index] = replacement
            page.update()
        except Exception as exc:
            self.show_message(page, f"❌ Не удалось повторно загрузить {name}: {exc}", COLORS.RED_700)

    def safe_tab(self, builder, page, name):
        try:
            return builder(page)
        except Exception as exc:
            message = f"{name}: {type(exc).__name__}: {exc}"
            self.config_error = message
            return ft.Column(
                controls=[
                    ft.Text(f"❌ {name} не удалось загрузить", size=18, weight=ft.FontWeight.BOLD, color=COLORS.RED_400),
                    ft.Text(str(exc), color="#B3FFFFFF", selectable=True),
                    ft.Button(content="🔄  ПОВТОРИТЬ", on_click=lambda e, b=builder, n=name: self.retry_tab(b, page, n), bgcolor=self.theme["primary"], color=COLORS.BLACK),
                ],
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )

    def refresh_tabs(self, page):
        self.tab_view.controls = [
            self.safe_tab(self.create_main_tab, page, "Главная"),
            self.safe_tab(self.create_settings_tab, page, "Настройки"),
            self.safe_tab(self.create_autoreply_tab, page, "Автоответ"),
            self.safe_tab(self.create_history_tab, page, "История"),
            self.safe_tab(self.create_themes_tab, page, "Темы"),
            self.safe_tab(self.create_about_tab, page, "О проекте"),
        ]
        page.update()

    def main(self, page: ft.Page):
        self.page = page
        self.load_config_file(strict=False)
        page.title = "AutoStars Control"
        page.theme_mode = ft.ThemeMode.DARK

        def handle_page_error(e):
            message = str(getattr(e, "data", "Неизвестная ошибка Flet"))
            print(f"[Flet] {message}")
            if self.action_status is not None:
                self.action_status.value = f"❌ Ошибка интерфейса: {message}"
                self.action_status.color = COLORS.RED_400
                self.action_status.visible = True
                try:
                    self.action_status.update()
                except Exception:
                    pass

        page.on_error = handle_page_error
        page.window.width = 1180
        page.window.height = 820
        page.window.min_width = 760
        page.window.min_height = 620
        page.window.resizable = True
        page.window.maximizable = True
        icon_path = resource_path("ico.ico")
        if not icon_path.exists():
            icon_path = user_path("ico.ico")
        if icon_path.exists():
            page.window.icon = str(icon_path)
        self.apply_theme(page, self.current_theme)
        page.padding = 14
        page.on_resize = lambda e: page.update()

        self.nav_icons = [
            ft.Icon(ICONS.HOME, color=self.theme.get("nav", "#B9BEC7")),
            ft.Icon(ICONS.SETTINGS, color=self.theme.get("nav", "#B9BEC7")),
            ft.Icon(ICONS.SMARTPHONE, color=self.theme.get("nav", "#B9BEC7")),
            ft.Icon(ICONS.INSERT_CHART, color=self.theme.get("nav", "#B9BEC7")),
            ft.Icon(ICONS.BRUSH, color=self.theme.get("nav", "#B9BEC7")),
            ft.Icon(ICONS.INFO, color=self.theme.get("nav", "#B9BEC7")),
        ]
        self.tab_bar = ft.TabBar(
            scrollable=True,
            indicator_color=self.theme["primary"],
            label_color=self.theme["primary"],
            unselected_label_color=self.theme.get("nav", "#B9BEC7"),
            divider_color=COLORS.TRANSPARENT,
            on_click=self.update_nav_colors,
            tabs=[
                ft.Tab(label="Главная", icon=self.nav_icons[0]),
                ft.Tab(label="Настройки", icon=self.nav_icons[1]),
                ft.Tab(label="Автоответ", icon=self.nav_icons[2]),
                ft.Tab(label="История", icon=self.nav_icons[3]),
                ft.Tab(label="Темы", icon=self.nav_icons[4]),
                ft.Tab(label="О проекте", icon=self.nav_icons[5]),
            ],
        )
        self.tab_view = ft.TabBarView(
            expand=True,
            controls=[
                self.safe_tab(self.create_main_tab, page, "Главная"),
                self.safe_tab(self.create_settings_tab, page, "Настройки"),
                self.safe_tab(self.create_autoreply_tab, page, "Автоответ"),
                self.safe_tab(self.create_history_tab, page, "История"),
                self.safe_tab(self.create_themes_tab, page, "Темы"),
                self.safe_tab(self.create_about_tab, page, "О проекте"),
            ],
        )
        self.tabs = ft.Tabs(
            selected_index=0,
            length=6,
            expand=True,
            content=ft.Column([self.tab_bar, self.tab_view], expand=True),
        )
        background = self.create_particles(page)
        page.add(
            ft.Stack(
                expand=True,
                controls=[
                    background,
                    ft.Container(content=ft.SafeArea(content=self.tabs, expand=True), expand=True),
                ],
            )
        )


def main():
    ft.run(AutoStarsGUI().main, assets_dir=str(RESOURCE_DIR))


if __name__ == "__main__":
    main()
