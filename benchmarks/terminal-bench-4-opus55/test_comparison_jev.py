import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from comparison_jev import ComparisonJev, JevFailure, arbiter, read_jev_journal
from comparison_accounting import AccountingError
from jev_host import jev_key_scope

IDENTITY = {"method": "git-overlay-v1", "task": "html-js-filter", "arm": "ticket-driver-c3a", "trial": "fake"}
QUESTION = {"ok": {"type": "noul", "instructions": "Is the supplied fixture valid?"}}


class ComparisonJevTests(unittest.TestCase):
    def fixture(self, root, transport):
        key = root / "key.env"
        key.write_text("test-only-jev-credential-not-real", encoding="utf8")
        judge = ComparisonJev(root / "jev.jsonl", IDENTITY, admit=lambda: None, transport=transport)
        return judge, key

    def test_exact_version_no_child_key_and_attributable_estimate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            calls = []
            def transport(request, **kwargs):
                self.assertNotIn("TYPESAFE_API_KEY", os.environ)
                calls.append(json.loads(request.data))
                self.assertEqual(calls[-1]["model"], "jev-1.13.0")
                rows = [json.loads(line) for line in (root / "jev.jsonl").read_text().splitlines()]
                self.assertEqual(rows[-1]["event"], "request")
                return io.BytesIO(json.dumps({"answers": {"ok": {"type": "noul", "noul": 0.99}},
                    "usage": {"input_tokens": 100, "output_tokens": 20}}).encode())
            judge, key = self.fixture(root, transport)
            with patch.dict(os.environ, {}, clear=True), jev_key_scope(key, arbiter.isolated_key):
                answers = judge.ask({"fixture": True}, QUESTION)
            self.assertEqual(answers["ok"]["noul"], 0.99)
            self.assertEqual(len(calls), 1)
            self.assertEqual(judge.receipt()["cost_usd"], "0.000004200")
            self.assertEqual(read_jev_journal(root / "jev.jsonl", IDENTITY)["cost_usd"], "0.000004200")
            self.assertNotIn(key.read_text(), (root / "jev.jsonl").read_text())
            rows = [json.loads(line) for line in (root / "jev.jsonl").read_text().splitlines()]
            rows[-1]["cost_usd"] = "0"
            (root / "jev.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
            with self.assertRaises(AccountingError):
                read_jev_journal(root / "jev.jsonl", IDENTITY)

    def test_http_failure_is_one_request_unknown_and_blocks_later_judgments(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            calls = []
            def transport(request, **kwargs):
                calls.append(request)
                raise urllib.error.HTTPError(request.full_url, 429, "synthetic", {}, None)
            judge, key = self.fixture(root, transport)
            with patch.dict(os.environ, {}, clear=True), jev_key_scope(key, arbiter.isolated_key):
                with self.assertRaises(JevFailure):
                    judge.ask({}, QUESTION)
                with self.assertRaises(JevFailure):
                    judge.ask({}, QUESTION)
            self.assertEqual(len(calls), 1)
            self.assertIsNone(judge.receipt()["cost_usd"])

    def test_invalid_typed_answer_keeps_attributable_usage_but_does_not_approve(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            def transport(request, **kwargs):
                return io.BytesIO(json.dumps({"answers": {}, "usage": {"input_tokens": 100, "output_tokens": 20}}).encode())
            judge, key = self.fixture(root, transport)
            with patch.dict(os.environ, {}, clear=True), jev_key_scope(key, arbiter.isolated_key):
                with self.assertRaises(JevFailure):
                    judge.ask({}, QUESTION)
            self.assertTrue(judge.receipt()["known"])
            self.assertEqual(judge.receipt()["requests"], 1)
            self.assertEqual(judge.receipt()["cost_usd"], "0.000004200")

    def test_wrong_arm_or_oversized_state_never_sends(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(JevFailure):
                ComparisonJev(root / "bad.jsonl", {**IDENTITY, "arm": "pi-bare"}, admit=lambda: None)
            judge, key = self.fixture(root, lambda *args, **kwargs: self.fail("network entered"))
            with patch.dict(os.environ, {}, clear=True), jev_key_scope(key, arbiter.isolated_key):
                with self.assertRaises(JevFailure):
                    judge.ask({"oversized": "x" * 25000}, QUESTION)
            self.assertEqual(judge.receipt()["requests"], 0)


if __name__ == "__main__":
    unittest.main()
