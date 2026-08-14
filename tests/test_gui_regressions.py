from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

GUI = PROJECT_ROOT / "gui.py"
SOURCE = GUI.read_text(encoding="utf-8")


class GUIRegressionTests(unittest.TestCase):
    def test_field_accepts_responsive_col(self):
        self.assertIn("def field(self, label, value, password=False, multiline=False, min_lines=None, max_lines=None, col=None):", SOURCE)
        self.assertIn("control.col = col", SOURCE)

    def test_autoreply_uses_field_col(self):
        self.assertIn('self.field("ЗАДЕРЖКА ПЕРЕД ОТВЕТОМ, СЕК"', SOURCE)
        self.assertIn('self.field("ПРАВИЛА JSON"', SOURCE)

    def test_retry_rebuilds_selected_tab(self):
        self.assertIn("def retry_tab(self, builder, page, name):", SOURCE)
        self.assertIn("self.tab_view.controls[index] = replacement", SOURCE)
        self.assertIn('on_click=lambda e, b=builder, n=name: self.retry_tab(b, page, n)', SOURCE)

    def test_no_deprecated_page_launch_url(self):
        self.assertNotIn("page.launch_url(", SOURCE)


if __name__ == "__main__":
    unittest.main()
