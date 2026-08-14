import asyncio
import base64
import html
import json
import logging
import shutil
from logging.handlers import RotatingFileHandler
import re
import random
import sqlite3
import sys
import threading
import time
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

import httpx
import requests
from FunPayAPI import Account, Runner, enums
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage


if getattr(sys, "frozen", False):
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    APP_DIR = Path(sys.executable).resolve().parent
else:
    RESOURCE_DIR = Path(__file__).resolve().parent
    APP_DIR = RESOURCE_DIR
BASE_DIR = APP_DIR
LOGGER = logging.getLogger("autostars")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(BASE_DIR / "autostars.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"),
        ],
    )


def ensure_config_file() -> Path:
    path = BASE_DIR / "config.json"
    example_path = RESOURCE_DIR / "config.example.json"
    if not example_path.exists():
        example_path = BASE_DIR / "config.example.json"
    if not path.exists():
        if not example_path.exists():
            raise RuntimeError("Файл config.json не найден, а config.example.json отсутствует.")
        shutil.copyfile(example_path, path)
        LOGGER.warning("config.json не найден — создана копия config.example.json. Заполните её через настройки.")
    return path


def load_config() -> dict:
    path = ensure_config_file()
    try:
        with path.open("r", encoding="utf-8") as file:
            config = json.load(file)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Ошибка чтения config.json: {exc}") from exc

    validate_config(config)
    return config


def validate_config(config: dict):
    required_sections = ("PAYMENT", "FRAGMENT", "BOT", "FUNPAY", "SETTINGS", "AUTOREPLY")
    for section in required_sections:
        if not isinstance(config.get(section), dict):
            raise RuntimeError(f"В config.json отсутствует раздел {section}.")

    required_values = (
        ("PAYMENT", "api_key"),
        ("PAYMENT", "mnemonic"),
        ("PAYMENT", "destination_address"),
        ("PAYMENT", "allowed_quantities"),
        ("PAYMENT", "is_testnet"),
        ("PAYMENT", "toncenter_url"),
        ("PAYMENT", "confirmation_attempts"),
        ("PAYMENT", "confirmation_delay"),
        ("FRAGMENT", "cookie"),
        ("FRAGMENT", "url"),
        ("BOT", "enabled"),
        ("FUNPAY", "golden_key"),
        ("SETTINGS", "db_path"),
        ("SETTINGS", "request_timeout"),
        ("SETTINGS", "order_check_interval"),
        ("AUTOREPLY", "enabled"),
        ("AUTOREPLY", "delay"),
        ("AUTOREPLY", "cooldown"),
        ("AUTOREPLY", "rules"),
    )
    for section, key in required_values:
        if key not in config[section]:
            raise RuntimeError(f"В config.json отсутствует параметр {section}.{key}.")

    if int(config["SETTINGS"]["request_timeout"]) <= 0:
        raise RuntimeError("SETTINGS.request_timeout должен быть больше 0.")
    if int(config["SETTINGS"]["order_check_interval"]) < 1:
        raise RuntimeError("SETTINGS.order_check_interval должен быть не меньше 1.")
    if int(config["BOT"]["enabled"]) and not config["BOT"].get("bot_token"):
        raise RuntimeError("BOT.bot_token обязателен, если BOT.enabled = 1.")
    if not isinstance(config["PAYMENT"]["mnemonic"], list) or len(config["PAYMENT"]["mnemonic"]) not in (12, 24):
        raise RuntimeError("PAYMENT.mnemonic должен содержать 12 или 24 слова.")
    if not isinstance(config["PAYMENT"]["allowed_quantities"], list) or not config["PAYMENT"]["allowed_quantities"]:
        raise RuntimeError("PAYMENT.allowed_quantities должен быть непустым списком.")
    try:
        quantities = [int(value) for value in config["PAYMENT"]["allowed_quantities"]]
    except (TypeError, ValueError) as exc:
        raise RuntimeError("PAYMENT.allowed_quantities должен содержать только целые числа.") from exc
    if any(value <= 0 for value in quantities) or len(set(quantities)) != len(quantities):
        raise RuntimeError("PAYMENT.allowed_quantities должен содержать уникальные положительные значения.")
    if int(config["PAYMENT"]["confirmation_attempts"]) < 1:
        raise RuntimeError("PAYMENT.confirmation_attempts должен быть не меньше 1.")
    if float(config["PAYMENT"]["confirmation_delay"]) < 0:
        raise RuntimeError("PAYMENT.confirmation_delay не может быть отрицательным.")
    if float(config["PAYMENT"].get("min_balance_reserve", 0.05)) < 0:
        raise RuntimeError("PAYMENT.min_balance_reserve не может быть отрицательным.")
    if str(config["PAYMENT"].get("payment_method", "ton")).casefold() != "ton":
        raise RuntimeError("PAYMENT.payment_method должен быть ton для текущей standalone TON-оплаты.")
    if not isinstance(config["PAYMENT"]["is_testnet"], bool):
        raise RuntimeError("PAYMENT.is_testnet должен быть JSON boolean: true или false.")
    wallet_address = str(config["PAYMENT"].get("wallet_address", "")).strip()
    if wallet_address and not wallet_address.startswith("YOUR_"):
        try:
            canonical_ton_address(wallet_address)
        except ValueError as exc:
            raise RuntimeError(f"PAYMENT.wallet_address имеет неверный формат: {exc}") from exc
    try:
        json.loads(str(config["PAYMENT"]["device"]))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"PAYMENT.device содержит некорректный JSON: {exc}") from exc
    if not str(config["FRAGMENT"].get("url", "https://fragment.com/api")).startswith("https://fragment.com/api"):
        raise RuntimeError("FRAGMENT.url должен указывать на https://fragment.com/api")
    cookie_value = config["FRAGMENT"].get("cookie", "")
    if isinstance(cookie_value, dict):
        cookie_items = {str(key): str(value) for key, value in cookie_value.items() if str(value).strip()}
    else:
        cookie_text = str(cookie_value or "").strip()
        try:
            parsed_cookie = json.loads(cookie_text) if cookie_text.startswith("{") else None
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"FRAGMENT.cookie содержит некорректный JSON: {exc}") from exc
        if isinstance(parsed_cookie, dict):
            cookie_items = {str(key): str(value) for key, value in parsed_cookie.items() if str(value).strip()}
        else:
            cookie_items = {part.split("=", 1)[0].strip(): part.split("=", 1)[1].strip() for part in cookie_text.split(";") if "=" in part and part.split("=", 1)[0].strip() and part.split("=", 1)[1].strip()}
    if not str(cookie_value or "").strip() or str(cookie_value).strip().startswith("YOUR_"):
        raise RuntimeError("FRAGMENT.cookie не настроен.")
    missing_cookie_keys = [key for key in ("stel_ssid", "stel_dt", "stel_token", "stel_ton_token") if key not in cookie_items]
    if missing_cookie_keys:
        raise RuntimeError(f"FRAGMENT.cookie не содержит обязательные cookies: {', '.join(missing_cookie_keys)}")
    if int(config["FRAGMENT"].get("min_stars", 50)) < 50:
        raise RuntimeError("FRAGMENT.min_stars не может быть меньше 50.")
    if int(config["FRAGMENT"].get("max_stars", 10000000)) < int(config["FRAGMENT"].get("min_stars", 50)):
        raise RuntimeError("FRAGMENT.max_stars должен быть не меньше FRAGMENT.min_stars.")
    if float(config["FRAGMENT"].get("rate_limit_delay", 1)) < 0.2:
        raise RuntimeError("FRAGMENT.rate_limit_delay должен быть не меньше 0.2 секунды.")
    toncenter_url = str(config["PAYMENT"]["toncenter_url"]).rstrip("/")
    expected_toncenter = "https://testnet.toncenter.com/api/v3/traces" if bool(config["PAYMENT"]["is_testnet"]) else "https://toncenter.com/api/v3/traces"
    if toncenter_url.startswith("https://preview.toncenter.com"):
        raise RuntimeError("PAYMENT.toncenter_url использует устаревший preview.toncenter.com. Укажите mainnet или testnet endpoint TON Center.")
    if toncenter_url != expected_toncenter:
        raise RuntimeError(f"PAYMENT.toncenter_url не соответствует PAYMENT.is_testnet. Ожидается: {expected_toncenter}")
    if float(config["AUTOREPLY"]["delay"]) < 0:
        raise RuntimeError("AUTOREPLY.delay не может быть отрицательным.")
    if int(config["AUTOREPLY"]["cooldown"]) < 0:
        raise RuntimeError("AUTOREPLY.cooldown не может быть отрицательным.")
    if int(config["AUTOREPLY"].get("poll_interval", 2)) < 1:
        raise RuntimeError("AUTOREPLY.poll_interval должен быть не меньше 1.")
    if not isinstance(config["AUTOREPLY"]["rules"], list):
        raise RuntimeError("AUTOREPLY.rules должен быть списком.")
    for rule in config["AUTOREPLY"]["rules"]:
        if not isinstance(rule, dict):
            raise RuntimeError("Каждое правило AUTOREPLY должно быть объектом.")
        triggers = rule.get("triggers")
        if isinstance(triggers, str):
            triggers = [triggers]
        if not isinstance(triggers, list) or not triggers or any(not str(trigger).strip() for trigger in triggers):
            raise RuntimeError("Каждое правило AUTOREPLY должно содержать непустой triggers.")
        response = str(rule.get("response", "")).strip()
        if not response:
            raise RuntimeError("Каждое правило AUTOREPLY должно содержать response.")
        if str(rule.get("match", "contains")).casefold() not in {"contains", "exact", "regex"}:
            raise RuntimeError("AUTOREPLY.match может быть только contains, exact или regex.")
        if str(rule.get("match", "contains")).casefold() == "regex":
            for trigger in triggers:
                try:
                    re.compile(str(trigger), re.IGNORECASE)
                except re.error as exc:
                    raise RuntimeError(f"Некорректный regex в AUTOREPLY: {exc}") from exc


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    def __init__(self, db_path: str):
        configured_path = BASE_DIR / db_path
        if configured_path.suffix.lower() == ".json":
            self.path = configured_path.with_suffix(".db")
            self.legacy_path = configured_path
        else:
            self.path = configured_path
            self.legacy_path = configured_path.with_name("db.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()
        self._migrate_json_if_needed()
        self._recover_processing_orders()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA foreign_keys=ON")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self):
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    admin_id INTEGER,
                    status TEXT NOT NULL,
                    login TEXT,
                    stars INTEGER,
                    amount INTEGER,
                    total_stars INTEGER,
                    ton_amount REAL,
                    ton_destination TEXT,
                    buyer_username TEXT,
                    tx_hash TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL UNIQUE,
                    login TEXT NOT NULL,
                    stars INTEGER NOT NULL,
                    tx_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(order_id) REFERENCES orders(order_id)
                );
                CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
                CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);
                """
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(orders)").fetchall()}
            if "ton_amount" not in columns:
                connection.execute("ALTER TABLE orders ADD COLUMN ton_amount REAL")
            if "ton_destination" not in columns:
                connection.execute("ALTER TABLE orders ADD COLUMN ton_destination TEXT")

    def _migrate_json_if_needed(self):
        legacy_path = self.legacy_path
        if not legacy_path.exists() or legacy_path == self.path:
            return
        with self._connect() as connection:
            existing_count = connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        if existing_count:
            return
        try:
            with legacy_path.open("r", encoding="utf-8") as file:
                legacy = json.load(file)
        except (OSError, json.JSONDecodeError):
            LOGGER.warning("Не удалось прочитать старую db.json для миграции.")
            return

        now = utc_now()
        with self._connect() as connection:
            for admin_id, data in legacy.items():
                try:
                    admin_value = int(admin_id) if admin_id not in (None, "None") else None
                except ValueError:
                    admin_value = None
                for order_id in data.get("succorders", []):
                    connection.execute(
                        "INSERT OR IGNORE INTO orders(order_id, admin_id, status, created_at, updated_at) VALUES(?,?,?,?,?)",
                        (str(order_id), admin_value, "completed", now, now),
                    )
                for payment in data.get("payment_history", []):
                    order_number = str(payment.get("order_number", "")).lstrip("#")
                    if not order_number:
                        continue
                    tx_hash = str(payment.get("tx_hash", "N/A"))
                    connection.execute(
                        "INSERT OR IGNORE INTO orders(order_id, admin_id, status, login, total_stars, tx_hash, created_at, updated_at) VALUES(?,?,?,?,?,?,?,?)",
                        (order_number, admin_value, "completed", payment.get("login"), payment.get("original_amount"), tx_hash, payment.get("date") or now, now),
                    )
                    connection.execute(
                        "INSERT OR IGNORE INTO transactions(order_id, login, stars, tx_hash, created_at) VALUES(?,?,?,?,?)",
                        (order_number, payment.get("login") or "", int(payment.get("original_amount") or 0), tx_hash, payment.get("date") or now),
                    )

    def _recover_processing_orders(self):
        with self._connect() as connection:
            connection.execute(
                "UPDATE orders SET status='unknown', error='Приложение было остановлено во время обработки заказа; проверьте транзакцию вручную.', updated_at=? WHERE status='processing'",
                (utc_now(),),
            )


    def get_order(self, order_id: str) -> Optional[dict]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM orders WHERE order_id = ?", (str(order_id),)).fetchone()
            return dict(row) if row else None

    def upsert_order(self, order_id: str, admin_id: Optional[int], status: str, login: Optional[str] = None, stars: Optional[int] = None, amount: Optional[int] = None, total_stars: Optional[int] = None, ton_amount: Optional[float] = None, buyer_username: Optional[str] = None, error: Optional[str] = None, ton_destination: Optional[str] = None):
        now = utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO orders(order_id, admin_id, status, login, stars, amount, total_stars, ton_amount, ton_destination, buyer_username, error, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(order_id) DO UPDATE SET
                    admin_id=excluded.admin_id,
                    status=excluded.status,
                    login=COALESCE(excluded.login, orders.login),
                    stars=COALESCE(excluded.stars, orders.stars),
                    amount=COALESCE(excluded.amount, orders.amount),
                    total_stars=COALESCE(excluded.total_stars, orders.total_stars),
                    ton_amount=COALESCE(excluded.ton_amount, orders.ton_amount),
                    ton_destination=COALESCE(excluded.ton_destination, orders.ton_destination),
                    buyer_username=COALESCE(excluded.buyer_username, orders.buyer_username),
                    error=excluded.error,
                    updated_at=excluded.updated_at
                """,
                (str(order_id), admin_id, status, login, stars, amount, total_stars, ton_amount, ton_destination, buyer_username, error, now, now),
            )

    def set_ton_amount(self, order_id: str, ton_amount: float):
        with self._connect() as connection:
            connection.execute("UPDATE orders SET ton_amount=?, updated_at=? WHERE order_id=?", (float(ton_amount), utc_now(), str(order_id)))

    def set_ton_destination(self, order_id: str, ton_destination: str):
        with self._connect() as connection:
            connection.execute("UPDATE orders SET ton_destination=?, updated_at=? WHERE order_id=?", (str(ton_destination), utc_now(), str(order_id)))

    def get_unknown_orders(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM orders WHERE status='unknown' AND tx_hash IS NOT NULL AND tx_hash != '' ORDER BY updated_at ASC").fetchall()
            return [dict(row) for row in rows]

    def mark_completed(self, order_id: str, login: str, total_stars: int, tx_hash: str):
        now = utc_now()
        with self._connect() as connection:
            connection.execute("UPDATE orders SET status='completed', tx_hash=?, error=NULL, updated_at=? WHERE order_id=?", (tx_hash, now, str(order_id)))
            connection.execute(
                "INSERT OR IGNORE INTO transactions(order_id, login, stars, tx_hash, created_at) VALUES(?,?,?,?,?)",
                (str(order_id), login, total_stars, tx_hash, now),
            )

    def mark_status(self, order_id: str, status: str, error: Optional[str] = None, tx_hash: Optional[str] = None):
        with self._connect() as connection:
            connection.execute(
                "UPDATE orders SET status=?, error=?, tx_hash=COALESCE(?, tx_hash), updated_at=? WHERE order_id=?",
                (status, error, tx_hash, utc_now(), str(order_id)),
            )

    def get_stats(self) -> dict:
        with self._connect() as connection:
            orders = connection.execute("SELECT COUNT(*) FROM orders WHERE status='completed'").fetchone()[0]
            stars = connection.execute("SELECT COALESCE(SUM(stars), 0) FROM transactions").fetchone()[0]
            failed = connection.execute("SELECT COUNT(*) FROM orders WHERE status='failed'").fetchone()[0]
            unknown = connection.execute("SELECT COUNT(*) FROM orders WHERE status='unknown'").fetchone()[0]
            return {"orders": orders, "stars": stars, "failed": failed, "unknown": unknown}

    def get_history(self, limit: int = 100) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(row) for row in rows]

    def get_legacy_view(self) -> dict:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM orders ORDER BY updated_at DESC").fetchall()
            transactions = connection.execute("SELECT * FROM transactions ORDER BY id DESC").fetchall()
        admin_id = None
        if rows:
            admin_id = rows[0]["admin_id"]
        return {
            str(admin_id): {
                "succorders": [row["order_id"] for row in rows if row["status"] == "completed"],
                "payment_history": [
                    {
                        "order_number": f"#{row['order_id']}",
                        "amount_dollar": 0,
                        "original_amount": row["stars"],
                        "currency": "stars",
                        "login": row["login"],
                        "date": row["created_at"],
                        "tx_hash": row["tx_hash"],
                    }
                    for row in transactions
                ],
            }
        }


try:
    from tonutils.client import TonapiClient
    from tonutils.wallet import WalletV4R2
    TONUTILS_AVAILABLE = True
    TONUTILS_IMPORT_ERROR = None
except ImportError as exc:
    TonapiClient = None
    WalletV4R2 = None
    TONUTILS_AVAILABLE = False
    TONUTILS_IMPORT_ERROR = exc


def canonical_ton_address(address: str) -> str:
    value = str(address or "").strip()
    if not value:
        raise ValueError("Пустой TON-адрес.")
    if ":" in value:
        workchain, account = value.split(":", 1)
        if re.fullmatch(r"-?\d+", workchain) and re.fullmatch(r"[0-9a-fA-F]{64}", account):
            return f"{int(workchain)}:{account.lower()}"
    try:
        raw = base64.urlsafe_b64decode(value + "=" * ((4 - len(value) % 4) % 4))
    except Exception as exc:
        raise ValueError("Некорректный TON-адрес.") from exc
    if len(raw) != 36:
        raise ValueError("Некорректный user-friendly TON-адрес.")
    workchain = raw[1] - 256 if raw[1] >= 128 else raw[1]
    return f"{workchain}:{raw[2:34].hex()}"


class FragmentStarsProcessor:
    def __init__(self, config: dict):
        if not TONUTILS_AVAILABLE:
            raise RuntimeError("Не удалось импортировать tonutils. Выполните: python -m pip install -r requirements.txt") from TONUTILS_IMPORT_ERROR
        self.payment = config["PAYMENT"]
        self.fragment = config["FRAGMENT"]
        self.timeout = int(config["SETTINGS"]["request_timeout"])
        self.min_stars = int(self.fragment.get("min_stars", 50))
        self.max_stars = int(self.fragment.get("max_stars", 10_000_000))
        self.rate_limit_delay = max(0.0, float(self.fragment.get("rate_limit_delay", 1.0)))
        self.retry_attempts = max(1, int(self.fragment.get("retry_attempts", 3)))
        self._request_lock = asyncio.Lock()
        self._last_request_at = 0.0
        self._hash_cache: Optional[str] = None
        self._hash_cache_at = 0.0
        self._hash_cache_ttl = max(30.0, float(self.fragment.get("hash_cache_ttl", 300)))
        self._last_payment_destination: Optional[str] = None
        self.fragment_page = str(self.fragment.get("stars_page", "https://fragment.com/stars/buy"))
        self.cookies = self._parse_cookies(self.fragment.get("cookie", ""))
        self.headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://fragment.com",
            "Referer": self.fragment_page,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
            "X-Requested-With": "XMLHttpRequest",
            "X-Aj-Referer": self.fragment_page.rsplit("/", 1)[0],
        }

    @staticmethod
    def _parse_cookies(value: object) -> dict[str, str]:
        if isinstance(value, dict):
            cookies = {str(key): str(item) for key, item in value.items() if str(item).strip()}
        else:
            text = str(value or "").strip()
            if not text:
                return {}
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                cookies = {}
                for part in text.split(";"):
                    if "=" in part:
                        key, item = part.strip().split("=", 1)
                        if key.strip() and item.strip():
                            cookies[key.strip()] = item.strip()
            else:
                if not isinstance(parsed, dict):
                    raise ValueError("FRAGMENT.cookie должен быть Cookie header или JSON-объектом.")
                cookies = {str(key): str(item) for key, item in parsed.items() if str(item).strip()}
        return cookies

    def _decode_payload(self, data: str) -> bytes:
        value = str(data or "").strip()
        value += "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(value)

    def _extract_ref_id(self, data: bytes) -> str:
        decoded = data.decode("latin1", errors="ignore")
        patterns = (
            r"Ref#([A-Za-z0-9_-]+)",
            r"Ref%23([A-Za-z0-9_-]+)",
        )
        for pattern in patterns:
            match = re.search(pattern, decoded)
            if match:
                return match.group(1)
        raise RuntimeError("В payload Fragment отсутствует Ref ID.")

    async def _wait_slot(self):
        async with self._request_lock:
            loop = asyncio.get_running_loop()
            wait_for = self.rate_limit_delay - (loop.time() - self._last_request_at)
            if wait_for > 0:
                await asyncio.sleep(wait_for)
            self._last_request_at = loop.time()

    def _request_sync(self, method: str, payload: Optional[dict] = None, page_url: Optional[str] = None, fragment_hash: Optional[str] = None):
        if method == "GET_PAGE":
            response = requests.get(
                self.fragment_page,
                headers={
                    key: value
                    for key, value in self.headers.items()
                    if key not in {"Content-Type", "Origin", "X-Requested-With", "X-Aj-Referer"}
                } | {"Referer": self.fragment_page.rsplit("/", 1)[0]},
                cookies=self.cookies,
                timeout=self.timeout,
            )
        else:
            response = requests.post(
                f"https://fragment.com/api?hash={fragment_hash}",
                headers={**self.headers, "Referer": page_url or self.fragment_page},
                cookies=self.cookies,
                data=payload or {},
                timeout=self.timeout,
            )
        return response

    async def _get_fragment_hash(self, force: bool = False) -> str:
        now = time.monotonic()
        if not force and self._hash_cache and now - self._hash_cache_at < self._hash_cache_ttl:
            return self._hash_cache
        configured = str(self.fragment.get("hash", "")).strip()
        try:
            await self._wait_slot()
            response = await asyncio.to_thread(self._request_sync, "GET_PAGE")
            response.raise_for_status()
            match = re.search(r"(?:https://fragment\.com)?\\?/api\?hash=([a-f0-9]+)", response.text)
            if match:
                self._hash_cache = match.group(1)
                self._hash_cache_at = now
                return self._hash_cache
        except Exception as exc:
            if not configured or configured.startswith("YOUR_"):
                raise RuntimeError(f"Не удалось получить актуальный API hash Fragment: {exc}") from exc
            LOGGER.warning("Не удалось получить динамический hash Fragment, используется fallback из конфигурации: %s", exc)
        if configured and not configured.startswith("YOUR_"):
            self._hash_cache = configured
            self._hash_cache_at = now
            return configured
        raise RuntimeError("Не удалось получить API hash Fragment со страницы покупки Stars.")

    async def _post_async(self, payload: dict, page_url: Optional[str] = None) -> dict:
        last_error = None
        for attempt in range(self.retry_attempts):
            try:
                fragment_hash = await self._get_fragment_hash(force=attempt > 0)
                await self._wait_slot()
                response = await asyncio.to_thread(self._request_sync, "POST", payload, page_url or self.fragment_page, fragment_hash)
                if response.status_code == 429:
                    last_error = RuntimeError("Fragment вернул HTTP 429 (rate limit).")
                elif response.status_code >= 500:
                    last_error = RuntimeError(f"Fragment вернул HTTP {response.status_code}.")
                else:
                    response.raise_for_status()
                    try:
                        data = response.json()
                    except json.JSONDecodeError as exc:
                        raise RuntimeError(f"Fragment вернул некорректный JSON: {response.text[:500]}") from exc
                    if not isinstance(data, dict):
                        raise RuntimeError("Fragment вернул JSON не в виде объекта.")
                    return data
            except (requests.RequestException, RuntimeError) as exc:
                last_error = exc
                if attempt + 1 < self.retry_attempts:
                    await asyncio.sleep(min(8.0, 1.0 + attempt * 2.0))
                    continue
                raise RuntimeError(f"Ошибка запроса Fragment: {last_error}") from exc
        raise RuntimeError(f"Ошибка запроса Fragment: {last_error}")

    def _create_wallet(self):
        def create():
            client = TonapiClient(api_key=self.payment["api_key"], is_testnet=self.payment["is_testnet"])
            return WalletV4R2.from_mnemonic(client, self.payment["mnemonic"])
        return create()

    async def _wallet_and_account_info(self):
        def build():
            client = TonapiClient(api_key=self.payment["api_key"], is_testnet=self.payment["is_testnet"])
            wallet, public_key, _, _ = WalletV4R2.from_mnemonic(client, self.payment["mnemonic"])
            boc = wallet.state_init.serialize().to_boc()
            account = {
                "address": wallet.address.to_str(False, False),
                "publicKey": public_key.as_hex,
                "chain": "-239",
                "walletStateInit": base64.b64encode(boc).decode(),
            }
            return wallet, account
        return await asyncio.to_thread(build)

    async def check_wallet_balance(self) -> float:
        wallet, _ = await self._wallet_and_account_info()
        balance = await wallet.balance()
        return float(balance)

    async def send_ton_transaction(self, destination: str, amount_nano: int, body) -> tuple[Optional[str], Optional[str], Optional[str]]:
        wallet, _ = await self._wallet_and_account_info()
        balance_nano = int(await wallet.balance())
        reserve_nano = int((Decimal(str(self.payment.get("min_balance_reserve", 0.05))) * Decimal("1000000000")).to_integral_value())
        if balance_nano < amount_nano + reserve_nano:
            required = Decimal(amount_nano + reserve_nano) / Decimal("1000000000")
            available = Decimal(balance_nano) / Decimal("1000000000")
            return None, None, f"Недостаточно средств на кошельке с учётом резерва. Требуется минимум {required} TON, доступно {available} TON."
        try:
            amount_ton = amount_nano / 1_000_000_000
            tx_hash = await wallet.transfer(
                destination=destination,
                amount=amount_ton,
                body=body,
            )
        except Exception as exc:
            return None, None, f"Не удалось однозначно определить результат отправки TON: {exc}"
        normalized_hash = getattr(tx_hash, "normalized_hash", None)
        return str(normalized_hash or tx_hash), None, None

    @staticmethod
    def _is_retryable_error(error: object) -> bool:
        text = str(error or "").casefold()
        return any(token in text for token in ("http 429", "http 502", "http 503", "http 504", "timed out", "timeout", "connection reset", "temporarily", "rate limit"))

    async def buy(self, username: str, quantity: int) -> tuple[str, Optional[str], Optional[str], int, Optional[float]]:
        self._last_payment_destination = None
        if not isinstance(quantity, int) or not self.min_stars <= quantity <= self.max_stars:
            return "failed", None, f"Количество Stars должно быть от {self.min_stars} до {self.max_stars}.", quantity, None
        clean_username = username.strip().lstrip("@")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{4,31}", clean_username):
            return "failed", None, "Некорректный Telegram username.", quantity, None
        try:
            search = await self._post_async(
                {"method": "searchStarsRecipient", "query": clean_username, "quantity": ""},
                self.fragment_page,
            )
            error_text = str(search.get("error", ""))
            if "assigned to a user" in error_text.casefold():
                return "failed", None, "Fragment сообщает, что username не привязан к пользователю.", quantity, None
            recipient = search.get("found", {}).get("recipient")
            if not recipient:
                return "failed", None, "Fragment не вернул recipient.", quantity, None

            await self._post_async(
                {
                    "method": "updateStarsBuyState",
                    "mode": "new",
                    "lv": "false",
                    "dh": str(random.randint(100_000_000, 2_147_483_647)),
                },
                self.fragment_page,
            )
            init = await self._post_async(
                {"method": "initBuyStarsRequest", "recipient": recipient, "quantity": quantity, "payment_method": self.payment.get("payment_method", "ton")},
                self.fragment_page,
            )
            try:
                init_amount = Decimal(str(init.get("amount")))
            except (InvalidOperation, TypeError, ValueError):
                init_amount = Decimal("0")
            req_id = init.get("req_id")
            if not req_id or init_amount <= 0:
                return "failed", None, f"Fragment не вернул корректные req_id/amount: {init}", quantity, None

            _, account = await self._wallet_and_account_info()
            link = await self._post_async(
                {
                    "method": "getBuyStarsLink",
                    "account": json.dumps(account, separators=(",", ":")),
                    "device": self.payment.get("device") or "{}",
                    "transaction": 1,
                    "id": req_id,
                    "show_sender": int(str(self.payment.get("show_sender", "0")) == "1"),
                },
                self.fragment_page,
            )
            if link.get("need_verify"):
                return "failed", None, "Fragment требует дополнительную верификацию аккаунта.", quantity, float(init_amount)
            messages = link.get("transaction", {}).get("messages", [])
            if not messages:
                return "failed", None, "Fragment не вернул сообщение транзакции.", quantity, float(init_amount)
            message = messages[0]
            payload = message.get("payload")
            destination = str(message.get("address") or "").strip()
            try:
                amount_nano = int(message.get("amount"))
            except (TypeError, ValueError):
                return "failed", None, "Fragment вернул некорректную сумму транзакции.", quantity, float(init_amount)
            if amount_nano <= 0 or not destination or not payload:
                return "failed", None, "Fragment вернул неполную транзакцию.", quantity, float(init_amount)
            configured_destination = str(self.payment.get("destination_address", "")).strip()
            if configured_destination and not configured_destination.startswith("YOUR_"):
                if canonical_ton_address(configured_destination) != canonical_ton_address(destination):
                    return "failed", None, "Адрес платежа Fragment не совпадает с разрешённым PAYMENT.destination_address.", quantity, float(init_amount)
            init_nano = int((init_amount * Decimal("1000000000")).to_integral_value())
            if init_nano != amount_nano:
                return "failed", None, "Сумма initBuyStarsRequest не совпадает с суммой готовой TON-транзакции.", quantity, float(init_amount)
            try:
                decoded_payload = self._decode_payload(payload)
                ref_id = self._extract_ref_id(decoded_payload)
                from pytoniq_core import Cell
                body = Cell.one_from_boc(decoded_payload)
            except Exception as exc:
                return "failed", None, f"Не удалось разобрать payload Fragment: {exc}", quantity, float(init_amount)
            self._last_payment_destination = destination
            tx_hash, _, tx_error = await self.send_ton_transaction(destination, amount_nano, body)
            if tx_error:
                if tx_error.startswith("Не удалось однозначно определить результат отправки TON:"):
                    return "unknown", None, tx_error, quantity, amount_nano / 1_000_000_000
                return "failed", None, tx_error, quantity, amount_nano / 1_000_000_000
            if not tx_hash:
                return "unknown", None, "TON не вернул hash транзакции.", quantity, amount_nano / 1_000_000_000
            return "sent", tx_hash, None, quantity, amount_nano / 1_000_000_000
        except Exception as exc:
            LOGGER.exception("Ошибка Fragment purchase для %s / %s Stars", clean_username, quantity)
            status = "retryable" if self._is_retryable_error(exc) else "failed"
            return status, None, str(exc), quantity, None

    def _trace_root(self, trace: dict) -> dict:
        nested = trace.get("trace")
        return nested if isinstance(nested, dict) else trace

    def _trace_nodes(self, node: dict):
        yield node
        children = node.get("children", [])
        if isinstance(children, list):
            for child in children:
                if isinstance(child, dict):
                    yield from self._trace_nodes(child)

    def _trace_transactions(self, trace: dict):
        root = self._trace_root(trace)
        for node in self._trace_nodes(root):
            transaction = node.get("transaction")
            if isinstance(transaction, dict):
                yield transaction

    def _trace_is_finalized_and_successful(self, trace: dict, expected_amount: Optional[float], expected_destination: Optional[str]) -> tuple[bool, bool, str]:
        if not isinstance(trace, dict):
            return False, False, "Некорректная структура trace."
        if trace.get("emulated") is True or trace.get("is_incomplete") is True:
            return False, False, "Trace ещё не финализирован."
        trace_info = trace.get("trace_info") or {}
        try:
            if int(trace_info.get("pending_messages") or 0) > 0:
                return False, False, "У trace остаются ожидающие сообщения."
        except (TypeError, ValueError):
            pass
        transactions = list(self._trace_transactions(trace))
        if not transactions:
            return False, False, "В trace ещё нет транзакций."
        expected_destination_canonical = canonical_ton_address(expected_destination) if expected_destination else None
        expected_nano = None
        if expected_amount is not None:
            expected_nano = int((Decimal(str(expected_amount)) * Decimal("1000000000")).to_integral_value())
        matching_out_message = False
        for transaction in transactions:
            if transaction.get("emulated") is True:
                return False, False, "В trace присутствует эмулированная транзакция."
            incoming = transaction.get("in_msg") or {}
            if incoming.get("bounced") is True:
                return True, False, "Входящее сообщение было возвращено."
            description = transaction.get("description") or {}
            if description.get("aborted") is True:
                return True, False, "Транзакция была прервана."
            compute = description.get("compute_ph") or {}
            if compute and compute.get("skipped") is not True and compute.get("success") is False:
                return True, False, "Compute phase завершилась ошибкой."
            action = description.get("action") or {}
            if action and action.get("success") is False:
                return True, False, "Action phase завершилась ошибкой."
            for out_message in transaction.get("out_msgs") or []:
                if not isinstance(out_message, dict):
                    continue
                destination = out_message.get("destination")
                try:
                    destination_canonical = canonical_ton_address(destination) if destination else None
                except ValueError:
                    destination_canonical = None
                if expected_destination_canonical and destination_canonical != expected_destination_canonical:
                    continue
                if expected_nano is not None:
                    try:
                        value_nano = int(out_message.get("value", 0))
                    except (TypeError, ValueError):
                        continue
                    if value_nano != expected_nano:
                        continue
                matching_out_message = True
        root = self._trace_root(trace)
        for child in root.get("children", []) or []:
            if not isinstance(child, dict):
                return True, False, "Trace содержит некорректный дочерний узел."
            child_final, child_success, child_error = self._trace_is_finalized_and_successful(child, None, None)
            if not child_final:
                return False, False, child_error
            if not child_success:
                return True, False, child_error
        if expected_destination_canonical and not matching_out_message:
            return True, False, "Не найден исходящий платёж на ожидаемый адрес с ожидаемой суммой."
        return True, True, ""

    async def confirm_transaction(self, tx_hash: str, expected_amount: Optional[float] = None, expected_destination: Optional[str] = None, attempts_override: Optional[int] = None) -> tuple[str, Optional[str]]:
        endpoint = self.payment["toncenter_url"]
        last_error = None
        attempts = max(1, int(attempts_override if attempts_override is not None else self.payment.get("confirmation_attempts", 25)))
        delay = max(0.5, float(self.payment.get("confirmation_delay", 5)))
        for attempt in range(attempts):
            try:
                def request():
                    with httpx.Client(timeout=self.timeout) as client:
                        return client.get(endpoint, params={"msg_hash": tx_hash, "include_actions": "false", "limit": 10})
                response = await asyncio.to_thread(request)
                if response.status_code == 404:
                    last_error = "Сообщение пока не найдено в индексаторе."
                else:
                    response.raise_for_status()
                    data = response.json()
                    traces = data.get("traces", [])
                    if not traces:
                        last_error = "Индексатор пока не вернул trace."
                    else:
                        for trace in traces:
                            finalized, successful, trace_error = self._trace_is_finalized_and_successful(trace, expected_amount, expected_destination)
                            if finalized and successful:
                                return "success", None
                            if finalized and not successful:
                                return "failed", trace_error
                            last_error = trace_error
            except Exception as exc:
                last_error = str(exc)
            if attempt + 1 < attempts:
                await asyncio.sleep(delay)
        return "unknown", last_error or "Транзакция не подтверждена."

    async def preflight_fragment(self, test_username: Optional[str] = None) -> tuple[bool, str]:
        try:
            fragment_hash = await self._get_fragment_hash(force=True)
            if not test_username:
                return True, f"Fragment API hash получен: {fragment_hash[:8]}..."
            username = test_username.strip().lstrip("@")
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{4,31}", username):
                return False, "FRAGMENT.test_username имеет неверный формат."
            result = await self._post_async({"method": "searchStarsRecipient", "query": username, "quantity": ""}, self.fragment_page)
            if result.get("found", {}).get("recipient"):
                return True, "Fragment успешно подтвердил доступ к поиску получателя."
            return False, str(result.get("error") or "Fragment не вернул получателя.")
        except Exception as exc:
            return False, str(exc)

    async def deliver(self, username: str, quantity: int) -> tuple[str, Optional[str], Optional[str], int, Optional[float]]:
        status, tx_hash, error, delivered_quantity, ton_amount = await self.buy(username, quantity)
        if status == "sent" and tx_hash:
            confirmation_status, confirmation_error = await self.confirm_transaction(tx_hash, ton_amount, self._last_payment_destination or self.payment.get("destination_address"))
            if confirmation_status == "success":
                return "success", tx_hash, None, delivered_quantity, ton_amount
            if confirmation_status == "failed":
                return "failed", tx_hash, confirmation_error, delivered_quantity, ton_amount
            return "unknown", tx_hash, confirmation_error, delivered_quantity, ton_amount
        if status == "unknown":
            return "unknown", tx_hash, error, delivered_quantity, ton_amount
        if status == "retryable":
            return "retryable", tx_hash, error, delivered_quantity, ton_amount
        return "failed", tx_hash, error, delivered_quantity, ton_amount


class AutoResponder:
    def __init__(self, config: dict):
        self.config = config
        self._stop = threading.Event()
        self._seen: set[str] = set()
        self._seen_order: list[str] = []
        self._cooldowns: dict[str, float] = {}

    @property
    def enabled(self) -> bool:
        return bool(int(self.config["AUTOREPLY"].get("enabled", 0)))

    def start(self):
        self._stop.clear()

    def stop(self):
        self._stop.set()

    def _remember(self, key: str) -> bool:
        if key in self._seen:
            return False
        self._seen.add(key)
        self._seen_order.append(key)
        if len(self._seen_order) > 5000:
            old = self._seen_order.pop(0)
            self._seen.discard(old)
        return True

    def _match_rule(self, text: str, rule: dict) -> bool:
        triggers = rule.get("triggers", [])
        if isinstance(triggers, str):
            triggers = [triggers]
        normalized = text.casefold()
        match_mode = str(rule.get("match", "contains")).casefold()
        if match_mode == "exact":
            return any(normalized == str(trigger).casefold() for trigger in triggers)
        if match_mode == "regex":
            return any(re.search(str(trigger), text, re.IGNORECASE) for trigger in triggers)
        return any(str(trigger).casefold() in normalized for trigger in triggers)

    def _get_response(self, text: str) -> Optional[str]:
        for rule in self.config["AUTOREPLY"].get("rules", []):
            if not isinstance(rule, dict):
                continue
            response = str(rule.get("response", "")).strip()
            if response and self._match_rule(text, rule):
                return response
        return None

    def handle_message(self, message, account: Account):
        if not self.enabled or self._stop.is_set() or not message:
            return
        author_id = getattr(message, "author_id", None)
        if author_id in {0, getattr(account, "id", None)}:
            return
        text = str(getattr(message, "text", "") or "").strip()
        if not text:
            return
        message_id = getattr(message, "id", None)
        chat_id = getattr(message, "chat_id", None)
        if chat_id is None:
            return
        key = f"{chat_id}:{message_id}:{text}"
        if not self._remember(key):
            return
        response = self._get_response(text)
        if response is None:
            return
        now = time.monotonic()
        cooldown = int(self.config["AUTOREPLY"].get("cooldown", 30))
        cooldown_key = str(chat_id)
        if cooldown and now - self._cooldowns.get(cooldown_key, 0) < cooldown:
            return
        self._cooldowns[cooldown_key] = now
        delay = float(self.config["AUTOREPLY"].get("delay", 0))
        if delay and self._stop.wait(delay):
            return
        username = getattr(message, "author", "") or ""
        response = response.replace("{username}", str(username)).replace("{chat_id}", str(chat_id))
        try:
            account.send_message(chat_id, response)
        except Exception:
            LOGGER.exception("Ошибка автоответчика в чате %s", chat_id)


class SingleInstanceLock:
    def __init__(self, path: Path):
        self.path = path
        self.handle = None

    def acquire(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("a+")
        try:
            if sys.platform.startswith("win"):
                import msvcrt
                self.handle.seek(0)
                self.handle.write("0")
                self.handle.flush()
                self.handle.seek(0)
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, IOError):
            self.handle.close()
            self.handle = None
            raise RuntimeError("AutoStars уже запущен в другом процессе.")

    def release(self):
        if not self.handle:
            return
        try:
            if sys.platform.startswith("win"):
                import msvcrt
                self.handle.seek(0)
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        except (OSError, IOError):
            pass
        try:
            self.handle.close()
        finally:
            self.handle = None



class StarBot:
    def __init__(self, config: dict):
        validate_config(config)
        self.config = config
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None
        self.storage = MemoryStorage()
        self.bot_config = config["BOT"]
        self.funpay_config = config["FUNPAY"]
        self.settings = config["SETTINGS"]
        self.database = Database(self.settings["db_path"])
        self.stop_event = asyncio.Event()
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._check_task: Optional[asyncio.Task] = None
        self._order_lock = asyncio.Lock()
        self._funpay_account: Optional[Account] = None
        self._funpay_runner_thread: Optional[threading.Thread] = None
        self._funpay_runner_stop = threading.Event()
        self._funpay_error_last_sent = 0.0
        self.payment = FragmentStarsProcessor(config)
        self.autoresponder = AutoResponder(config)
        self.startup_event = threading.Event()
        self.startup_error: Optional[str] = None
        self.ready = False
        self.instance_lock = SingleInstanceLock(BASE_DIR / ".autostars.lock")

    async def load_db(self) -> dict:
        return self.database.get_legacy_view()

    async def save_db(self, db: dict):
        return None

    async def extract_order_info(self, description: str, order_html: str = "") -> tuple[Optional[str], Optional[int], int]:
        description = description if isinstance(description, str) else ""
        order_html = order_html if isinstance(order_html, str) else ""
        login = None
        login_match = re.search(r"(?<![A-Za-z0-9_])@([A-Za-z][A-Za-z0-9_]{4,31})\b", description)
        if login_match:
            login = login_match.group(1)
        else:
            parts = [part.strip().lstrip("@") for part in description.split(",") if part.strip()]
            for candidate in reversed(parts):
                if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{4,31}", candidate):
                    login = candidate
                    break
        stars_match = re.search(r"(?<!\d)(\d+)\s*(?:зв(?:ёзд|езд|езды|ёзды)?|stars?)\b", description, re.IGNORECASE)
        stars = int(stars_match.group(1)) if stars_match else None
        quantity_patterns = (
            r"(?:количеств(?:о|а)|quantity|qty)\s*[:=]?\s*(\d+)",
            r"(?<!\d)(\d+)\s*шт\.?\b",
            r"(?:x|×)\s*(\d+)(?!\d)",
        )
        quantity = 1
        quantity_sources = (description, re.sub(r"<[^>]+>", " ", order_html))
        for source in quantity_sources:
            for pattern in quantity_patterns:
                match = re.search(pattern, source, re.IGNORECASE)
                if match:
                    quantity = int(match.group(1))
                    break
            if quantity > 1:
                break
        return login, stars, max(1, quantity)

    async def send_funpay_message(self, account: Account, username: str, message: str) -> bool:
        try:
            chat = await asyncio.to_thread(account.get_chat_by_name, username, make_request=True)
            if not chat or not getattr(chat, "id", None):
                LOGGER.warning("Чат FunPay с %s не найден.", username)
                return False
            await asyncio.to_thread(account.send_message, chat_id=chat.id, text=message)
            return True
        except Exception:
            LOGGER.exception("Ошибка отправки сообщения в FunPay для %s", username)
            return False

    def create_telegram_message(self, order_id: str, login: str, stars: int, tx_hash: str) -> str:
        return (
            f"✨ <b>УСПЕШНАЯ ВЫДАЧА ЗВЁЗД</b> ✨\n\n"
            f"🆔 <b>Номер заказа:</b> <code>#{html.escape(str(order_id))}</code>\n"
            f"👤 <b>Получатель:</b> <code>@{html.escape(login)}</code>\n"
            f"⭐ <b>Количество звёзд:</b> <code>{stars} шт.</code>\n"
            f"📜 <b>Транзакция:</b> <code>{html.escape(str(tx_hash))}</code>\n\n"
            "✅ <b>Статус:</b> Выполнено успешно\n\n"
            "💬 <b>Для покупателя:</b>\n"
            "<i>Звёзды были автоматически зачислены на ваш аккаунт. Пожалуйста, подтвердите получение в чате FunPay.</i>\n\n"
            f"<a href='https://funpay.com/orders/{html.escape(str(order_id))}/'>🔗 Ссылка на заказ</a>"
        )

    def create_funpay_message(self, order_id: str, login: str, stars: int, tx_hash: str) -> str:
        return (
            f"🌟 [b]ВАШ ЗАКАЗ #[/b]{order_id} [b]ВЫПОЛНЕН![/b] 🌟\n\n"
            f"✔ [b]Получатель:[/b] @{login}\n"
            f"✔ [b]Количество звёзд:[/b] {stars} шт.\n"
            f"✔ [b]ID транзакции:[/b] {tx_hash}\n\n"
            "[i]Звёзды были автоматически зачислены на ваш аккаунт. Если возникли проблемы - свяжитесь с продавцом.[/i]\n\n"
            "[u]Пожалуйста, подтвердите получение:[/u]\n"
            "1. Нажмите \"Подтвердить выполнение заказа\"\n"
            "2. Оставьте отзыв о работе магазина\n\n"
            f"[url=https://funpay.com/orders/{order_id}/]ℹ Подробнее о заказе[/url]\n\n"
            "С уважением, AutoStars!"
        )

    def create_error_message(self, order_id: str, login: Optional[str], stars: Optional[int], error: str, status: str) -> str:
        return (
            f"⚠️ <b>ОШИБКА ПРИ ВЫДАЧЕ ЗВЁЗД</b> ⚠️\n\n"
            f"🆔 <b>Номер заказа:</b> <code>#{html.escape(str(order_id))}</code>\n"
            f"👤 <b>Получатель:</b> <code>@{html.escape(login or 'не определён')}</code>\n"
            f"⭐ <b>Количество звёзд:</b> <code>{stars or 'не определено'} шт.</code>\n\n"
            f"❌ <b>Статус:</b> <code>{html.escape(status)}</code>\n"
            f"<b>Ошибка:</b> <code>{html.escape(str(error)[:1500])}</code>\n\n"
            "🛠 <b>Проверьте данные заказа, Fragment и TON.</b>"
        )

    async def notify_admin(self, text: str):
        admin_id = self.settings.get("admin_telegram_id")
        if not admin_id or not self.bot:
            return
        try:
            await self.bot.send_message(chat_id=admin_id, text=text, parse_mode="HTML")
        except Exception:
            LOGGER.exception("Не удалось отправить уведомление администратору")


    async def _process_order(self, order, account: Account, admin_telegram_id: Optional[int]):
        order_id = str(getattr(order, "id", ""))
        if not order_id:
            return

        existing = self.database.get_order(order_id)
        if existing and existing["status"] in {"completed", "invalid", "unknown", "processing", "failed"}:
            return

        description = getattr(order, "description", "") or ""
        order_html = getattr(order, "html", "") or ""
        count = getattr(order, "amount", None)
        login, stars, parsed_count = await self.extract_order_info(description, order_html)
        if count is None:
            count = parsed_count
        count = max(1, int(count))
        if not login or not stars:
            try:
                full_order = await asyncio.to_thread(account.get_order, order_id)
                full_description = " ".join(filter(None, [getattr(full_order, "short_description", None), getattr(full_order, "full_description", None)]))
                full_login, full_stars, parsed_full_count = await self.extract_order_info(full_description, getattr(full_order, "html", ""))
                login = login or full_login
                stars = stars or full_stars
                full_amount = getattr(full_order, "amount", None)
                if getattr(order, "amount", None) is None and full_amount is not None:
                    count = full_amount
                elif getattr(order, "amount", None) is None and parsed_full_count > 1:
                    count = parsed_full_count
            except Exception:
                LOGGER.exception("Не удалось получить полную информацию о заказе %s", order_id)
        if not login or not stars:
            error = "Не удалось определить логин или количество звёзд."
            self.database.upsert_order(order_id, admin_telegram_id, "invalid", login, stars, count, None, None, getattr(order, "buyer_username", None), error)
            await self.notify_admin(self.create_error_message(order_id, login, stars, error, "invalid"))
            return

        allowed_lots = {int(value) for value in self.config["PAYMENT"].get("allowed_quantities", [])}
        if stars not in allowed_lots:
            error = f"Размер лота {stars} Stars отсутствует в PAYMENT.allowed_quantities."
            self.database.upsert_order(order_id, admin_telegram_id, "invalid", login, stars, count, stars * count, None, getattr(order, "buyer_username", None), error)
            await self.notify_admin(self.create_error_message(order_id, login, stars, error, "invalid"))
            return
        total_stars = stars * count
        buyer_username = getattr(order, "buyer_username", None)
        self.database.upsert_order(order_id, admin_telegram_id, "processing", login, stars, count, total_stars, None, buyer_username)

        result = "retryable"
        tx_hash = None
        error = None
        delivered_quantity = total_stars
        ton_amount = None
        retry_attempts = max(1, int(self.config["PAYMENT"].get("delivery_retry_attempts", 3)))
        retry_delay = max(1.0, float(self.config["PAYMENT"].get("delivery_retry_delay", 5)))
        for attempt in range(retry_attempts):
            result, tx_hash, error, delivered_quantity, ton_amount = await self.payment.deliver(login, total_stars)
            if result != "retryable":
                break
            if attempt + 1 < retry_attempts:
                await asyncio.sleep(retry_delay * (attempt + 1))
        if ton_amount is not None:
            self.database.set_ton_amount(order_id, ton_amount)
        if self.payment._last_payment_destination:
            self.database.set_ton_destination(order_id, self.payment._last_payment_destination)

        if result == "success":
            tx_hash = str(tx_hash or "N/A")
            self.database.mark_completed(order_id, login, delivered_quantity, tx_hash)
            await self.notify_admin(self.create_telegram_message(order_id, login, delivered_quantity, tx_hash))
            if buyer_username:
                await self.send_funpay_message(account, buyer_username, self.create_funpay_message(order_id, login, delivered_quantity, tx_hash))
            return

        if result == "retryable":
            status = "unknown"
            error_text = error or "Временная ошибка платёжного провайдера после повторных попыток."
            self.database.mark_status(order_id, status, error_text, tx_hash)
            await self.notify_admin(self.create_error_message(order_id, login, delivered_quantity, error_text, status))
            return
        status = "unknown" if result == "unknown" else "failed"
        error_text = error or "Неизвестная ошибка"
        self.database.mark_status(order_id, status, error_text, tx_hash)
        tx_info = f"\n🔗 <b>TX Hash:</b> <code>{html.escape(str(tx_hash))}</code>" if tx_hash else ""
        await self.notify_admin(self.create_error_message(order_id, login, delivered_quantity, error_text + tx_info, status))
        if status == "failed" and bool(self.config["PAYMENT"].get("auto_refund", False)):
            try:
                await asyncio.to_thread(account.refund, order_id)
                await self.notify_admin(f"↩️ <b>Заказ #{html.escape(order_id)} автоматически возвращён.</b>")
            except Exception:
                LOGGER.exception("Не удалось автоматически вернуть заказ %s", order_id)

    async def process_order(self, order, account: Account, admin_telegram_id: Optional[int]):
        async with self._order_lock:
            await self._process_order(order, account, admin_telegram_id)

    async def recheck_unknown_orders(self, account: Account, admin_telegram_id: Optional[int]):
        for order in self.database.get_unknown_orders():
            tx_hash = str(order.get("tx_hash") or "").strip()
            ton_amount = order.get("ton_amount")
            ton_destination = order.get("ton_destination") or self.config["PAYMENT"].get("destination_address")
            if not tx_hash or ton_amount is None or not ton_destination:
                continue
            try:
                status, error = await self.payment.confirm_transaction(tx_hash, float(ton_amount), ton_destination, attempts_override=1)
            except Exception as exc:
                LOGGER.exception("Ошибка повторной проверки заказа %s", order["order_id"])
                continue
            if status == "success":
                login = order.get("login") or ""
                total_stars = int(order.get("total_stars") or order.get("stars") or 0)
                self.database.mark_completed(order["order_id"], login, total_stars, tx_hash)
                await self.notify_admin(self.create_telegram_message(order["order_id"], login, total_stars, tx_hash))
                if order.get("buyer_username"):
                    await self.send_funpay_message(account, order["buyer_username"], self.create_funpay_message(order["order_id"], login, total_stars, tx_hash))
            elif status == "failed":
                self.database.mark_status(order["order_id"], "failed", error, tx_hash)
                await self.notify_admin(self.create_error_message(order["order_id"], order.get("login"), order.get("stars"), error or "Транзакция отклонена.", "failed"))

    async def get_funpay_account(self) -> Optional[Account]:
        try:
            account = Account(self.funpay_config["golden_key"], requests_timeout=int(self.settings["request_timeout"]))
            await asyncio.to_thread(account.get)
            return account
        except Exception:
            LOGGER.exception("Не удалось подключиться к FunPay")
            return None

    def _run_funpay_runner(self, account: Account):
        while not self._funpay_runner_stop.is_set() and not self.stop_event.is_set():
            try:
                runner = Runner(account)
                request_delay = max(1, int(self.settings.get("order_check_interval", 4)))
                for event in runner.listen(requests_delay=request_delay):
                    if self._funpay_runner_stop.is_set() or self.stop_event.is_set():
                        return
                    event_type = getattr(event, "type", None)
                    if event_type is enums.EventTypes.NEW_MESSAGE:
                        self.autoresponder.handle_message(getattr(event, "message", None), account)
                    elif event_type is enums.EventTypes.NEW_ORDER:
                        order = getattr(event, "order", None)
                        if order is not None and self.loop and not self.stop_event.is_set():
                            future = asyncio.run_coroutine_threadsafe(
                                self.process_order(order, account, self.settings.get("admin_telegram_id")),
                                self.loop,
                            )
                            future.add_done_callback(self._log_runner_future)
            except Exception as exc:
                if self._funpay_runner_stop.is_set() or self.stop_event.is_set():
                    return
                LOGGER.exception("FunPay Runner остановился: %s", exc)
                time.sleep(5)
                try:
                    account.get(update_phpsessid=True)
                except Exception:
                    LOGGER.exception("Не удалось обновить FunPay-сессию после ошибки Runner")

    @staticmethod
    def _log_runner_future(future):
        try:
            future.result()
        except Exception:
            LOGGER.exception("Ошибка обработки события FunPay")

    def start_funpay_runner(self):
        account = self._funpay_account
        if account is None or (self._funpay_runner_thread and self._funpay_runner_thread.is_alive()):
            return
        self._funpay_runner_stop.clear()
        self._funpay_runner_thread = threading.Thread(target=self._run_funpay_runner, args=(account,), name="FunPayRunner", daemon=True)
        self._funpay_runner_thread.start()

    def stop_funpay_runner(self):
        self._funpay_runner_stop.set()
        thread = self._funpay_runner_thread
        if thread and thread.is_alive():
            thread.join(timeout=10)
        self._funpay_runner_thread = None

    async def check_orders(self):
        admin_id = self.settings.get("admin_telegram_id")
        if not self.funpay_config.get("golden_key"):
            LOGGER.error("FunPay Golden Key не установлен.")
            return

        account = self._funpay_account
        last_account_refresh = time.monotonic()
        while not self.stop_event.is_set():
            try:
                if account is None:
                    account = await self.get_funpay_account()
                    if account is not None:
                        self._funpay_account = account
                        last_account_refresh = time.monotonic()
                elif time.monotonic() - last_account_refresh >= 45 * 60:
                    await asyncio.to_thread(account.get, True)
                    last_account_refresh = time.monotonic()
                if account is not None:
                    await self.recheck_unknown_orders(account, admin_id)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                account = None
                self._funpay_account = None
                LOGGER.exception("Ошибка в цикле проверки FunPay")
                await self.notify_admin(
                    f"⚠️ <b>Ошибка FunPay-чекера</b>\n<code>{html.escape(str(exc)[:1500])}</code>"
                )

            try:
                await asyncio.wait_for(self.stop_event.wait(), timeout=int(self.settings["order_check_interval"]))
            except asyncio.TimeoutError:
                pass


    async def preflight(self):
        if not self.funpay_config.get("golden_key") or str(self.funpay_config.get("golden_key")).startswith("YOUR_"):
            raise RuntimeError("FUNPAY.golden_key не настроен.")
        try:
            account = Account(self.funpay_config["golden_key"], requests_timeout=int(self.settings["request_timeout"]))
            await asyncio.to_thread(account.get)
            self._funpay_account = account
        except Exception as exc:
            raise RuntimeError(f"Не удалось подключиться к FunPay: {exc}") from exc

        if int(self.bot_config.get("enabled", 0)):
            token = str(self.bot_config.get("bot_token", ""))
            if not token or token.startswith("YOUR_"):
                raise RuntimeError("BOT.bot_token не настроен.")
            test_bot = Bot(token=token)
            try:
                await test_bot.get_me()
            except Exception as exc:
                raise RuntimeError(f"Не удалось подключиться к Telegram: {exc}") from exc
            finally:
                if not test_bot.session.closed:
                    await test_bot.session.close()

        payment_config = self.config["PAYMENT"]
        fragment_config = self.config["FRAGMENT"]
        try:
            if str(payment_config["api_key"]).startswith("YOUR_"):
                raise RuntimeError("PAYMENT.api_key не настроен.")
            if any(str(word).startswith("word") for word in payment_config["mnemonic"]):
                raise RuntimeError("PAYMENT.mnemonic содержит тестовые слова.")
            wallet_result = await asyncio.to_thread(self.payment._create_wallet)
            wallet = wallet_result[0] if isinstance(wallet_result, tuple) else wallet_result
            wallet_address = wallet.address.to_str()
            configured_wallet = str(payment_config.get("wallet_address", "")).strip()
            if configured_wallet and not configured_wallet.startswith("YOUR_") and canonical_ton_address(configured_wallet) != canonical_ton_address(wallet_address):
                raise RuntimeError(f"TON wallet не совпадает с PAYMENT.wallet_address. Фактический адрес: {wallet_address}")
            balance = await wallet.balance()
            if float(balance) <= 0:
                raise RuntimeError(f"TON-кошелёк пустой: {wallet_address}")
            configured_account = str(payment_config.get("account", "")).strip()
            if configured_account and not configured_account.startswith("YOUR_"):
                try:
                    account_data = json.loads(configured_account)
                    configured_account_address = str(account_data.get("address", "")).strip()
                    if configured_account_address and canonical_ton_address(configured_account_address) != canonical_ton_address(wallet_address):
                        raise RuntimeError("Старый PAYMENT.account не соответствует TON wallet. Удалите его или обновите конфигурацию.")
                except json.JSONDecodeError:
                    pass
        except Exception as exc:
            raise RuntimeError(f"TON не прошёл проверку: {exc}") from exc

        configured_destination = str(payment_config.get("destination_address", "")).strip()
        if configured_destination and not configured_destination.startswith("YOUR_"):
            try:
                canonical_ton_address(configured_destination)
            except ValueError as exc:
                raise RuntimeError(f"PAYMENT.destination_address имеет неверный формат: {exc}") from exc
        if not self.payment.cookies:
            raise RuntimeError("Данные Fragment cookie не настроены.")
        fragment_ok, fragment_message = await self.payment.preflight_fragment(fragment_config.get("test_username"))
        if not fragment_ok:
            raise RuntimeError(f"Fragment не прошёл проверку: {fragment_message}")

    async def stop(self):
        self.stop_event.set()
        self.ready = False
        self.stop_funpay_runner()
        self.autoresponder.stop()
        if self.dp:
            try:
                await self.dp.stop_polling()
            except RuntimeError:
                pass
        if self._check_task and not self._check_task.done():
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        if self.bot and not self.bot.session.closed:
            await self.bot.session.close()
        self.bot = None
        self.dp = None
        self._funpay_account = None
        self.instance_lock.release()

    async def start_bot(self):
        self.loop = asyncio.get_running_loop()
        self.stop_event.clear()
        self.startup_event.clear()
        self.startup_error = None
        self.ready = False
        try:
            self.instance_lock.acquire()
            await self.preflight()
            self._check_task = asyncio.create_task(self.check_orders())
            self.autoresponder.start()
            self.start_funpay_runner()
            self.ready = True
            self.startup_event.set()
        except Exception as exc:
            self.startup_error = str(exc)
            self.startup_event.set()
            LOGGER.exception("Предстартовая проверка не пройдена")
            await self.stop()
            return

        if not int(self.bot_config.get("enabled", 0)) or not self.bot_config.get("bot_token"):
            LOGGER.info("Telegram-бот отключён. FunPay-чекер продолжает работу.")
            try:
                await self.stop_event.wait()
            finally:
                await self.stop()
            return

        self.bot = Bot(token=self.bot_config["bot_token"])
        self.dp = Dispatcher(storage=self.storage)

        @self.dp.message(Command("start"))
        async def send_welcome(message: types.Message):
            admin_id = self.settings.get("admin_telegram_id")
            if admin_id and int(admin_id) == message.from_user.id:
                await message.answer(
                    "🤖 <b>AutoStars</b>\n\n"
                    "Автоматическая выдача звёзд через FunPay активна.\n"
                    "Используйте /help для краткой информации.",
                    parse_mode="HTML",
                )
                return
            await message.answer(
                "🤖 <b>AutoStars</b>\n\n"
                f"Ваш Telegram ID: <code>{message.from_user.id}</code>\n"
                "Добавьте этот ID в SETTINGS.admin_telegram_id, если хотите получать уведомления.",
                parse_mode="HTML",
            )

        @self.dp.message(Command("help"))
        async def send_help(message: types.Message):
            await message.answer(
                "<b>AutoStars</b>\n\n"
                "Бот автоматически проверяет заказы FunPay и выдаёт Stars через Fragment и TON.\n\n"
                "/start — информация о боте\n"
                "/help — эта справка",
                parse_mode="HTML",
            )

        await self.notify_admin("✅ <b>AutoStars запущен</b>\nFunPay-чекер активен.")
        try:
            await self.dp.start_polling(self.bot, handle_signals=False)
        finally:
            await self.stop()


if __name__ == "__main__":
    setup_logging()
    configuration = load_config()
    asyncio.run(StarBot(configuration).start_bot())
