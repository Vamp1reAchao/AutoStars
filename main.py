import re
import json
import aiohttp
import asyncio
from datetime import datetime
from FunPayAPI import Account
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command

def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Файл config.json не найден. Создайте его на основе примера.")
        exit(1)
    except json.JSONDecodeError:
        print("Ошибка чтения config.json. Проверьте синтаксис JSON.")
        exit(1)


class StarBot:
    def __init__(self, config: dict):
        self.config = config
        self.bot = None
        self.dp = None
        self.storage = MemoryStorage()
        self.api_config = self.config["API"]
        self.bot_config = self.config["BOT"]
        self.funpay_config = self.config["FUNPAY"]
        self.settings = self.config["SETTINGS"]

    async def load_db(self) -> dict:
        try:
            with open(self.settings["db_path"], "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"База данных не найдена по пути {self.settings['db_path']}. Создаем новую.")
            return {}
        except json.JSONDecodeError:
            print(f"Ошибка чтения базы данных по пути {self.settings['db_path']}. Создаем новую.")
            return {}

    async def save_db(self, db: dict):
        with open(self.settings["db_path"], "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)

    async def extract_order_info(self, description: str) -> tuple:
        try:
            login = None
            if "," in description:
                login = description.split(",")[-1].strip().lstrip("@")
          
            if not login:
                match = re.search(r"@([A-Za-z][A-Za-z0-9_]{4,31})", description)
                if match:
                    login = match.group(1)

            stars_match = re.search(r"(\d+)\s*зв", description, re.IGNORECASE)
            stars = int(stars_match.group(1)) if stars_match else None

            return login, stars

        except Exception as e:
            print(f"Ошибка при извлечении данных: {e}")
            return None, None

    async def send_funpay_message(self, account: Account, username: str, message: str) -> bool:
        try:
            chat = account.get_chat_by_name(username, make_request=True)
            if not chat or not hasattr(chat, 'id'):
                print(f"Чат с {username} не найден или неверный формат.")
                return False
          
            account.send_message(chat_id=chat.id, text=message)
            return True
        except Exception as e:
            print(f"Ошибка отправки сообщения в FunPay: {e}")
            return False

    async def create_telegram_message(self, order_id: str, login: str, stars: int, tx_hash: str) -> str:
        return (
            f"✨ <b>УСПЕШНАЯ ВЫДАЧА ЗВЁЗД</b> ✨\n\n"
            f"🆔 <b>Номер заказа:</b> <code>#{order_id}</code>\n"
            f"👤 <b>Получатель:</b> <code>@{login}</code>\n"
            f"⭐ <b>Количество звёзд:</b> <code>{stars} шт.</code>\n"
            f"📜 <b>Транзакция:</b> <code>{tx_hash}</code>\n\n"
            "✅ <b>Статус:</b> Выполнено успешно\n\n"
            "💬 <b>Для покупателя:</b>\n"
            "<i>Звёзды были автоматически зачислены на ваш аккаунт. "
            "Пожалуйста, подтвердите получение в чате FunPay.</i>\n\n"
            f"<a href='https://funpay.com/orders/{order_id}/'>🔗 Ссылка на заказ</a>"
        )

    async def create_funpay_message(self, order_id: str, login: str, stars: int, tx_hash: str) -> str:
        return (
            f"🌟 [b]ВАШ ЗАКАЗ #[/b]{order_id} [b]ВЫПОЛНЕН![/b] 🌟\n\n"
            f"✔ [b]Получатель:[/b] @{login}\n"
            f"✔ [b]Количество звёзд:[/b] {stars} шт.\n"
            f"✔ [b]ID транзакции:[/b] {tx_hash}\n\n"
            "[i]Звёзды были автоматически зачислены на ваш аккаунт. "
            "Если возникли проблемы - свяжитесь с продавцом.[/i]\n\n"
            "[u]Пожалуйста, подтвердите получение:[/u]\n"
            "1. Нажмите \"Подтвердить выполнение заказа\"\n"
            "2. Оставьте отзыв о работе магазина\n\n"
            f"[url=https://funpay.com/orders/{order_id}/]ℹ Подробнее о заказе[/url]\n\n"
            "С уважением, ваш магазин StarShop!"
        )

    async def create_error_message(self, order_id: str, login: str, stars: int, error: str) -> str:
        return (
            f"⚠️ <b>ОШИБКА ПРИ ВЫДАЧЕ ЗВЁЗД</b> ⚠️\n\n"
            f"🆔 <b>Номер заказа:</b> <code>#{order_id}</code>\n"
            f"👤 <b>Получатель:</b> <code>@{login}</code>\n"
            f"⭐ <b>Количество звёзд:</b> <code>{stars} шт.</code>\n\n"
            f"❌ <b>Ошибка:</b>\n<code>{error}</code>\n\n"
            "🛠 <b>Рекомендуемые действия:</b>\n"
            "1. Проверьте баланс звёзд\n"
            "2. Убедитесь в правильности логина\n"
            "3. Свяжитесь с технической поддержкой"
        )

    async def process_order(self, order, account: Account, admin_telegram_id: int):
        login, stars = await self.extract_order_info(order.description)
        if not login or not stars or stars < 50:
            print(f"Неверные данные заказа #{order.id}")
            db = await self.load_db()
            db.setdefault(str(admin_telegram_id), {}).setdefault("succorders", []).append(order.id)
            await self.save_db(db)
            return

        count = getattr(order, "amount", 1) or 1
        total_stars = stars * count
        buyer_username = getattr(order, "buyer_username", None)

        payload = {
            "username": login,
            "quantity": total_stars,
            "hide_sender": 1,
        }
        headers = {
            "accept": "application/json",
            "X-API-Token": self.api_config["token"],
            "Content-Type": "application/json",
        }

        db = await self.load_db()
        db.setdefault(str(admin_telegram_id), {}).setdefault("succorders", []).append(order.id)
        await self.save_db(db)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_config["url"],
                    json=payload,
                    headers=headers,
                    timeout=self.settings["request_timeout"]
                ) as resp:
                    response = await resp.json()

                    if resp.status == 200 and response.get("success"):
                        tx_hash = response.get("transfers", [{}])[0].get("tx_hash", "N/A")
                      
                        if admin_telegram_id:
                            tg_msg = await self.create_telegram_message(
                                order.id, login, total_stars, tx_hash
                            )
                            await self.bot.send_message(
                                chat_id=admin_telegram_id,
                                text=tg_msg,
                                parse_mode="HTML"
                            )

                        if buyer_username:
                            fp_msg = await self.create_funpay_message(
                                order.id, login, total_stars, tx_hash
                            )
                            await self.send_funpay_message(account, buyer_username, fp_msg)

                        shop_data = db.setdefault(str(admin_telegram_id), {})
                        shop_data.setdefault("payment_history", []).append({
                            "order_number": f"#{order.id}",
                            "amount_dollar": 0,
                            "original_amount": total_stars,
                            "currency": "stars",
                            "login": login,
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "tx_hash": tx_hash
                        })
                        await self.save_db(db)

                    else:
                        error_msg = response.get("error", "Неизвестная ошибка API")
                        if admin_telegram_id:
                            err_msg = await self.create_error_message(
                                order.id, login, total_stars, error_msg
                            )
                            await self.bot.send_message(
                                chat_id=admin_telegram_id,
                                text=err_msg,
                                parse_mode="HTML"
                            )

        except Exception as e:
            error_msg = f"Системная ошибка: {str(e)}"
            if admin_telegram_id:
                err_msg = await self.create_error_message(
                    order.id, login, total_stars, error_msg
                )
                await self.bot.send_message(
                    chat_id=admin_telegram_id,
                    text=err_msg,
                    parse_mode="HTML"
                )

    async def check_orders(self):
        admin_telegram_id = self.settings.get("admin_telegram_id")

        if not self.funpay_config["golden_key"]:
            print("FunPay Golden Key не установлен. Проверка заказов невозможна.")
            return

        while True:
            await asyncio.sleep(self.settings["order_check_interval"])
          
            try:
                account = Account(self.funpay_config["golden_key"])
                account.get()
              
                sells = account.get_sells()
                if not sells or len(sells) < 2:
                    continue

                orders = sells[1]
                excluded_statuses = {"REFUNDED", "CLOSED", "COMPLETED"}

                db = await self.load_db()
                processed_orders_for_user = db.setdefault(str(admin_telegram_id), {}).setdefault("succorders", [])

                for order in orders:
                    if not order or not hasattr(order, "id"):
                        continue

                    if str(order.status) in excluded_statuses:
                        continue

                    if order.id in processed_orders_for_user:
                        continue



                    await self.process_order(order, account, admin_telegram_id)

            except Exception as e:
                print(f"Ошибка в основном цикле проверки заказов FunPay: {e}")
                if admin_telegram_id:
                    try:
                        await self.bot.send_message(
                            chat_id=admin_telegram_id,
                            text=f"⚠️ <b>ВНИМАНИЕ: Ошибка в работе FunPay чекера!</b>\n\n<code>{e}</code>",
                            parse_mode="HTML"
                        )
                    except Exception as tg_e:
                        print(f"Не удалось отправить сообщение об ошибке в Telegram: {tg_e}")

    async def ping_api_server(self):
        ping_url = self.api_config.get("ping_url")
        api_token = self.api_config.get("token")

        if not ping_url:
            print("URL для пинга API не указан в конфигурации.")
            return False
        if not api_token:
            print("API Token не указан в конфигурации. Пинг API невозможен.")
            return False

        headers = {
            "accept": "application/json",
            "X-API-Token": api_token,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(ping_url, headers=headers, timeout=5) as resp:
                    response_json = await resp.json()
                    if resp.status == 200 and response_json.get("status") == True and response_json.get("message") == "pong":
                        print("✅ API сервер успешно пропингован: pong")
                        return True
                    else:
                        print(f"❌ API сервер ответил с ошибкой или неожиданным статусом: HTTP {resp.status}, Ответ: {response_json}")
                        return False
        except aiohttp.ClientError as e:
            print(f"❌ Ошибка подключения к API серверу при пинге: {e}")
            return False
        except Exception as e:
            print(f"❌ Неизвестная ошибка при пинге API сервера: {e}")
            return False

    async def start_bot(self):
        # Ping API server on startup
        print("Попытка пинга API сервера...")
        api_ok = await self.ping_api_server()
        if not api_ok:
            print("🔴 Не удалось подключиться к API серверу. Работа бота может быть нарушена.")
            # Decide if you want to exit or continue
            # For now, it will continue, but you might want to add sys.exit(1) here
            # or only proceed if API is available for critical functions.
        else:
            print("🟢 API сервер доступен.")

        if self.bot_config["enabled"] == 0:
            print("Запуск бота Telegram отключен в конфигурации (BOT -> enabled: 0).")
            if self.funpay_config["golden_key"]:
                print("Проверка заказов FunPay будет запущена без Telegram уведомлений.")
                asyncio.create_task(self.check_orders())
                while True:
                    await asyncio.sleep(3600)
            return

        if not self.bot_config["bot_token"]:
            print("Bot Token не найден в конфигурации. Бот Telegram не будет запущен.")
            if self.funpay_config["golden_key"]:
                print("Проверка заказов FunPay будет запущена без Telegram уведомлений.")
                asyncio.create_task(self.check_orders())
                while True:
                    await asyncio.sleep(3600)
            return

        self.bot = Bot(token=self.bot_config["bot_token"])
        self.dp = Dispatcher(storage=self.storage)

        @self.dp.message(Command("start"))
        async def send_welcome(message: types.Message):
            if not self.settings.get("admin_telegram_id"):
                self.settings["admin_telegram_id"] = message.from_user.id
                db = await self.load_db()
                db_for_admin = db.setdefault(str(message.from_user.id), {})
                db_for_admin.setdefault("succorders", [])
                db_for_admin.setdefault("payment_history", [])
                await self.save_db(db)
                print(f"Telegram ID администратора установлен: {message.from_user.id}")
                await message.answer(
                    f"Привет! Твой Telegram ID ({message.from_user.id}) был автоматически установлен как ID администратора для получения уведомлений. Теперь я буду присылать уведомления сюда."
                )
            else:
                await message.answer(
                    "🤖 <b>StarBot - автоматическая выдача звёзд FunPay</b>\n\n"
                    "Я автоматически проверяю новые заказы и выдаю звёзды.\n"
                    "Для работы необходимо:\n"
                    "1. Добавить golden_key в настройках (уже есть в коде)\n"
                    "2. Установить статус \"online\" на FunPay\n\n"
                    "🛠 Техподдержка: @support",
                    parse_mode="HTML"
                )

        asyncio.create_task(self.check_orders())

        try:
            print("Бот Telegram запущен и готов к приему команд...")
            print(f"Проверка заказов FunPay запущена с интервалом {self.settings['order_check_interval']} секунд.")
            if self.settings.get("admin_telegram_id"):
                print(f"Уведомления будут отправляться на Telegram ID: {self.settings['admin_telegram_id']}")
                await self.bot.send_message(
                    chat_id=self.settings["admin_telegram_id"],
                    text="✅ <b>StarBot успешно запущен и начал работу!</b>\n\n"
                         "Я буду отслеживать новые заказы на FunPay и автоматически выдавать звёзды. "
                         "Все уведомления об успешных выдачах и ошибках будут приходить сюда.",
                    parse_mode="HTML"
                )
            else:
                print("Администраторский Telegram ID не установлен. Пожалуйста, отправьте команду /start боту для его регистрации.")
              
            await self.dp.start_polling(self.bot)
        finally:
            await self.storage.close()
            await self.storage.wait_closed()
            print("Бот остановлен.")

if __name__ == "__main__":
    config = load_config()
    bot = StarBot(config)
    asyncio.run(bot.start_bot())