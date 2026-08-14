from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from tests._stubs import install_stubs

install_stubs()

import main


def build_config(db_path: str) -> dict:
    return {
        "PAYMENT": {
            "api_key": "test-api-key",
            "mnemonic": [f"w{i}" for i in range(24)],
            "destination_address": "0:" + "b" * 64,
            "allowed_quantities": [10, 25, 50, 100, 250],
            "is_testnet": False,
            "toncenter_url": "https://toncenter.com/api/v3/traces",
            "confirmation_attempts": 3,
            "confirmation_delay": 1,
                        "device": '{"platform":"android","appName":"Tonkeeper","appVersion":"5.0.18","maxProtocolVersion":2,"features":["SendTransaction",{"name":"SendTransaction","maxMessages":4}]}',
            "wallet_address": "",
            "min_balance_reserve": 0.05, "payment_method": "ton",
            "auto_refund": False,
            "show_sender": "0",
        },
        "FRAGMENT": {"hash": "fragment-hash", "cookie": "stel_ssid=test; stel_dt=test; stel_token=test; stel_ton_token=test", "url": "https://fragment.com/api"},
        "BOT": {"enabled": 1, "bot_token": "bot-token"},
        "FUNPAY": {"golden_key": "golden-key"},
        "SETTINGS": {"db_path": db_path, "request_timeout": 10, "order_check_interval": 10, "admin_telegram_id": 111},
        "AUTOREPLY": {"enabled": 0, "delay": 1, "cooldown": 30, "poll_interval": 2, "rules": [{"triggers": ["привет"], "match": "contains", "response": "Здравствуйте!"}]},
    }


class ConfigValidationTests(unittest.TestCase):
    def test_validate_config_accepts_valid_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = build_config(str(Path(tmp) / "autostars.db"))
            main.validate_config(config)

    def test_validate_config_requires_fragment_session_cookies(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = build_config(str(Path(tmp) / "autostars.db"))
            config["FRAGMENT"]["cookie"] = "only_one_cookie=value"
            with self.assertRaises(RuntimeError):
                main.validate_config(config)

    def test_validate_config_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = build_config(str(Path(tmp) / "autostars.db"))
            config["PAYMENT"]["device"] = "not-json"
            with self.assertRaises(RuntimeError):
                main.validate_config(config)


if __name__ == "__main__":
    unittest.main()
