from __future__ import annotations

import asyncio
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
from tests.test_config import build_config


class PreflightTests(unittest.TestCase):
    def test_preflight_passes_with_valid_stubs(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = build_config(str(Path(tmp) / "autostars.db"))
            config["PAYMENT"]["wallet_address"] = "0:" + "a" * 64
            bot = main.StarBot(config)
            async def fake_fragment_preflight(test_username=None):
                return True, "stub"
            bot.payment.preflight_fragment = fake_fragment_preflight
            asyncio.run(bot.preflight())
            self.assertIsNotNone(bot._funpay_account)



if __name__ == "__main__":
    unittest.main()
