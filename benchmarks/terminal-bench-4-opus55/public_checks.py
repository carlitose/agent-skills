"""Public, non-exhaustive smoke checks derived only from the task instructions.

Installed outside /app for every modified arm. These are neither the original
project suite nor Harbor's hidden verifier, and do not certify full correctness.
"""
import copy
import importlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

APP = Path("/app")


class HtmlEvents(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.events = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.events.append(("start", tag, sorted(attrs)))

    def handle_endtag(self, tag):
        self.events.append(("end", tag))

    def handle_data(self, text):
        self.events.append(("text", text))


class HtmlSmoke(unittest.TestCase):
    def filtered(self, source):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input.html"
            path.write_text(source, encoding="utf8")
            result = subprocess.run([sys.executable, str(APP / "filter.py"), str(path)],
                                    capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, "filter CLI must succeed")
            return path.read_text(encoding="utf8")

    def test_benign_structure_and_text_survive(self):
        text = '<h2>Heading</h2><table><tr><td title="safe">Data &amp; text</td></tr></table>'
        self.assertEqual(HtmlEvents(self.filtered(text)).events, HtmlEvents(text).events)

    def test_script_element_is_not_executable(self):
        events = HtmlEvents(self.filtered('<p>Keep me</p><script>alert(1)</script>')).events
        self.assertFalse(any(e[:2] == ("start", "script") for e in events))
        self.assertIn(("text", "Keep me"), events)

    def test_event_handler_removed_without_removing_legitimate_attribute(self):
        events = HtmlEvents(self.filtered('<p title="safe" onclick="alert(1)">Keep</p>')).events
        starts = [e for e in events if e[:2] == ("start", "p")]
        self.assertEqual(len(starts), 1)
        self.assertIn(("title", "safe"), starts[0][2])
        self.assertFalse(any(key.lower().startswith("on") for key, _ in starts[0][2]))


class CipherSmoke(unittest.TestCase):
    def invoke(self, *args):
        return subprocess.run([sys.executable, str(APP / "cracker.py"), *map(str, args)],
                              capture_output=True, timeout=30)

    def test_missing_argument_is_error(self):
        self.assertTrue((APP / "cracker.py").is_file())
        self.assertNotEqual(self.invoke().returncode, 0)

    def test_missing_file_is_error(self):
        self.assertTrue((APP / "cracker.py").is_file())
        with tempfile.TemporaryDirectory() as temp:
            self.assertNotEqual(self.invoke(Path(temp) / "absent.txt").returncode, 0)

    def test_public_development_sample(self):
        ciphertext = APP / "data/sample_ciphertext.txt"
        plaintext = (APP / "data/sample_plaintext.txt").read_bytes()
        result = self.invoke(ciphertext)
        self.assertEqual(result.returncode, 0, "cracker CLI must succeed")
        self.assertEqual(len(result.stdout), len(ciphertext.read_bytes()), "exact output length")
        self.assertEqual(result.stdout, plaintext, "public development sample only; not generalization proof")
        self.assertTrue((APP / "requirements.txt").is_file())


class WalSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(APP))
        cls.app = importlib.import_module("app")
        cls.recovery = importlib.import_module("recovery")
        cls.config = importlib.import_module("config")

    @staticmethod
    def snapshot():
        return {"segments": [
            {"segment_id": 9, "closed": True, "durable_count": 2, "entries": [
                {"segment_id": 9, "lsn": 2, "key": "b", "value": "loser"},
                {"segment_id": 9, "lsn": 1, "key": "a", "value": "first"}]},
            {"segment_id": 2, "closed": False, "durable_count": 1, "entries": [
                {"segment_id": 999, "lsn": 2, "key": "b", "value": {"nested": [1]}},
                {"segment_id": 2, "lsn": 3, "key": "not-durable", "value": "ignored"}]},
            {"segment_id": 7, "closed": True, "durable_count": 1, "entries": [
                {"segment_id": 7, "lsn": 4, "key": "after-gap", "value": "ignored"}]}]}

    def test_public_fields(self):
        self.assertTrue(callable(self.app.make_engine))
        self.assertEqual(set(self.config.RECOVERY_ENTRY_FIELDS), {"segment_id", "lsn", "key", "value"})
        self.assertEqual(set(self.config.RECOVERY_STATS_KEYS), {"segments_scanned", "replayed_entries", "last_lsn"})

    def test_durable_prefix_gap_duplicate_and_segment_order(self):
        for recover in (self.app.recover_engine, self.recovery.recover_from_snapshot):
            for reverse in (False, True):
                snapshot = self.snapshot()
                if reverse:
                    snapshot["segments"].reverse()
                original = copy.deepcopy(snapshot)
                state, replayed, stats = recover(snapshot)
                self.assertEqual(snapshot, original, "input must remain unchanged")
                self.assertEqual(state, {"a": "first", "b": {"nested": [1]}})
                self.assertEqual(replayed, [
                    {"segment_id": 9, "lsn": 1, "key": "a", "value": "first"},
                    {"segment_id": 2, "lsn": 2, "key": "b", "value": {"nested": [1]}}])
                self.assertEqual(stats, {"segments_scanned": 3, "replayed_entries": 2, "last_lsn": 2})

    def test_recovery_outputs_are_detached(self):
        snapshot = self.snapshot()
        original = copy.deepcopy(snapshot)
        for recover in (self.app.recover_engine, self.recovery.recover_from_snapshot):
            first = recover(snapshot)
            second = recover(snapshot)
            first[0]["b"]["nested"].append(7)
            self.assertEqual(first[1][1]["value"], {"nested": [1]})
            first[1][1]["value"]["nested"].append(8)
            first[2]["last_lsn"] = 99
            self.assertEqual(snapshot, original)
            self.assertEqual(second, recover(snapshot))

    def test_omitted_durable_count_replays_nothing(self):
        snapshot = {"segments": [{"segment_id": 1, "closed": True, "entries": [
            {"segment_id": 1, "lsn": 1, "key": "a", "value": "not durable"}]}]}
        for recover in (self.app.recover_engine, self.recovery.recover_from_snapshot):
            self.assertEqual(recover(snapshot), ({}, [], {
                "segments_scanned": 1, "replayed_entries": 0, "last_lsn": 0}))


def run(task):
    classes = {"html-js-filter": HtmlSmoke, "interleaved-vigenere": CipherSmoke,
               "wal-recovery-ordering": WalSmoke}
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(classes[task])
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=1).run(suite)
    passed = result.wasSuccessful() and result.testsRun > 0 and not result.skipped
    receipt = {"schema": 1, "task": task, "kind": "public-functional-smoke-not-official-verifier",
               "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
               "skipped": len(result.skipped), "passed": passed}
    print(json.dumps(receipt, sort_keys=True))
    if not passed:
        print(output.getvalue()[-8192:], file=sys.stderr)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1]))
