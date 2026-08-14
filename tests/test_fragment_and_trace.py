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


class FragmentAndTraceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.config = build_config(str(Path(self.tmp.name) / "autostars.db"))
        self.processor = main.FragmentStarsProcessor(self.config)

    def tearDown(self):
        self.tmp.cleanup()

    def test_buy_accepts_multi_lot_total_quantity(self):
        calls = []

        async def fake_post(payload, page_url=None):
            calls.append(payload)
            if payload["method"] == "searchStarsRecipient":
                return {"ok": True, "found": {"recipient": "recipient-id"}}
            if payload["method"] == "updateStarsBuyState":
                return {"ok": True}
            if payload["method"] == "initBuyStarsRequest":
                return {"ok": True, "req_id": "REQ123", "amount": 12.5}
            if payload["method"] == "getBuyStarsLink":
                return {
                    "ok": True,
                    "transaction": {
                        "messages": [
                            {
                                "payload": "UmVmI0FCQzEyMw==",
                                "address": "0:" + "b" * 64,
                                "amount": "12500000000",
                            }
                        ]
                    }
                }
            raise AssertionError(f"Unexpected payload: {payload}")

        async def fake_send(destination, amount_nano, body):
            return "tx-hash", None, None

        self.processor._post_async = fake_post
        self.processor.send_ton_transaction = fake_send

        class _Cell:
            @classmethod
            def one_from_boc(cls, data):
                return object()

        import sys, types
        pytoniq_core = types.ModuleType("pytoniq_core")
        pytoniq_core.Cell = _Cell
        sys.modules["pytoniq_core"] = pytoniq_core

        status, tx_hash, error, quantity, ton_amount = asyncio.run(self.processor.buy("@buyer", 750))
        self.assertEqual(status, "sent")
        self.assertEqual(tx_hash, "tx-hash")
        self.assertIsNone(error)
        self.assertEqual(quantity, 750)
        self.assertEqual(ton_amount, 12.5)
        self.assertEqual([p["method"] for p in calls], ["searchStarsRecipient", "updateStarsBuyState", "initBuyStarsRequest", "getBuyStarsLink"])

    def test_fragment_payload_helpers(self):
        self.assertEqual(self.processor._extract_ref_id(b"prefix Ref#ABC_123 suffix"), "ABC_123")
        self.assertEqual(self.processor._parse_cookies("stel_ssid=a; stel_dt=b; stel_token=c; stel_ton_token=d")["stel_token"], "c")

    def test_fragment_retryable_error_detection(self):
        self.assertTrue(self.processor._is_retryable_error("Fragment HTTP 429 rate limit"))
        self.assertTrue(self.processor._is_retryable_error("connection timed out"))
        self.assertFalse(self.processor._is_retryable_error("username not found"))

    def test_trace_parser_accepts_successful_trace(self):
        trace = {
            "emulated": False,
            "is_incomplete": False,
            "trace_info": {"pending_messages": 0},
            "trace": {
                "transaction": {
                    "emulated": False,
                    "in_msg": {"bounced": False},
                    "description": {
                        "aborted": False,
                        "compute_ph": {"skipped": False, "success": True},
                        "action": {"success": True},
                        "bounce": {"type": ""},
                    },
                    "out_msgs": [
                        {
                            "destination": "0:" + "b" * 64,
                            "value": "12500000000",
                        }
                    ],
                },
                "children": [],
            },
        }
        finalized, success, error = self.processor._trace_is_finalized_and_successful(trace, 12.5, "0:" + "b" * 64)
        self.assertTrue(finalized)
        self.assertTrue(success)
        self.assertEqual(error, "")

    def test_trace_parser_rejects_wrong_amount(self):
        trace = {
            "emulated": False,
            "is_incomplete": False,
            "trace_info": {"pending_messages": 0},
            "trace": {
                "transaction": {
                    "emulated": False,
                    "in_msg": {"bounced": False},
                    "description": {
                        "aborted": False,
                        "compute_ph": {"skipped": False, "success": True},
                        "action": {"success": True},
                        "bounce": {"type": ""},
                    },
                    "out_msgs": [
                        {
                            "destination": "0:" + "b" * 64,
                            "value": "1000000000",
                        }
                    ],
                },
                "children": [],
            },
        }
        finalized, success, error = self.processor._trace_is_finalized_and_successful(trace, 12.5, "0:" + "b" * 64)
        self.assertTrue(finalized)
        self.assertFalse(success)
        self.assertIn("ожидаемый", error.lower())



if __name__ == "__main__":
    unittest.main()
