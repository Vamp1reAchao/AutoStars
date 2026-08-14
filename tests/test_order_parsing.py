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


class OrderParsingTests(unittest.TestCase):
    def test_extract_order_info_parses_count_from_description_and_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            bot = main.StarBot(build_config(str(Path(tmp) / "autostars.db")))
            login, stars, count = asyncio.run(bot.extract_order_info("@buyer, 250 Stars, qty=3", "<div>3 шт.</div>"))
            self.assertEqual(login, "buyer")
            self.assertEqual(stars, 250)
            self.assertEqual(count, 3)

    def test_extract_order_info_falls_back_to_html_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            bot = main.StarBot(build_config(str(Path(tmp) / "autostars.db")))
            login, stars, count = asyncio.run(bot.extract_order_info("@buyer, 100 Stars", "<div>x2</div>"))
            self.assertEqual(login, "buyer")
            self.assertEqual(stars, 100)
            self.assertEqual(count, 2)


    def test_database_connection_is_closed_after_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "autostars.db"
            bot = main.StarBot(build_config(str(db_path)))
            bot.database.get_stats()
            db_path.unlink()



if __name__ == "__main__":
    unittest.main()
