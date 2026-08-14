# 🚀 Установка AutoStars

## Требования

- Windows 10/11 или Linux
- Python 3.10+
- Интернет-соединение
- Аккаунт FunPay с Golden Key
- Telegram-бот и токен от BotFather
- Fragment session cookies (`stel_ssid`, `stel_dt`, `stel_token`, `stel_ton_token`)
- TON API key
- TON-кошелёк с достаточным балансом
- Мнемоническая фраза кошелька

## Установка

1. Клонируйте репозиторий:

```bash
git clone https://github.com/yourusername/AutoStars.git
cd AutoStars
```

2. Установите зависимости:

```bash
python -m pip install -r requirements.txt
```

3. При первом запуске проект сам создаст `config.json` из `config.example.json`, если файла ещё нет.

4. Заполните `config.json`.

В разделе `PAYMENT` укажите TON API key, мнемонику, параметры TON-проверки и размеры лотов. `destination_address` можно оставить пустым: тогда адрес берётся непосредственно из подготовленного Fragment transaction. Если указать адрес, он используется как дополнительный allowlist.

В разделе `FRAGMENT` укажите актуальные session cookies. Hash Fragment проект получает автоматически; поле `hash` является только fallback.

В разделе `FUNPAY` укажите Golden Key.

В разделе `BOT` укажите Telegram Bot Token.

5. Запустите:

```bash
python main.py
```

Или:

```bash
python gui.py
```

В Windows можно использовать `start_gui.bat`.

## 🤖 Автоответчик

Автоответчик включается в `AUTOREPLY.enabled`.

Правила задаются в `AUTOREPLY.rules`.

Пример:

```json
{
  "enabled": 1,
  "delay": 1,
  "cooldown": 30,
  "poll_interval": 2,
  "rules": [
    {
      "triggers": ["привет", "здравствуйте"],
      "match": "contains",
      "response": "Здравствуйте, {username}! Чем могу помочь?"
    }
  ]
}
```

Изменить эти параметры можно через вкладку `🤖 АВТООТВЕТ` в GUI.

## 🔐 Безопасность

Никогда не публикуйте:

- `config.json`
- TON mnemonic
- Fragment cookie
- Fragment hash
- FunPay Golden Key
- Telegram Bot Token
- TON API key

Эти файлы и секреты не должны попадать в Git.

## 🗄️ База данных

Используется SQLite `autostars.db`.

Старая `db.json`, если она была создана предыдущей версией, переносится автоматически.

## ⚠️ Важно

При статусе `unknown` не запускайте повторную выдачу, пока не проверите TON-транзакцию. Это предотвращает двойную выдачу Stars.
