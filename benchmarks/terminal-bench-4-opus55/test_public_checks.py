"""Causal smoke-harness checks with synthetic products, not task solutions."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import public_checks


class PublicCheckTests(unittest.TestCase):
    def run_checks(self, root, task):
        stdout, stderr = io.StringIO(), io.StringIO()
        old_path = sys.path[:]
        try:
            with patch.object(public_checks, "APP", root), patch.dict(sys.modules), \
                    contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                for module in ("app", "recovery", "config"):
                    sys.modules.pop(module, None)
                code = public_checks.run(task)
        finally:
            sys.path[:] = old_path
        return code, json.loads(stdout.getvalue())

    def test_absent_products_fail_for_every_task_not_zero_test_success(self):
        with tempfile.TemporaryDirectory() as temp:
            for task in ("html-js-filter", "interleaved-vigenere", "wal-recovery-ordering"):
                with self.subTest(task=task):
                    code, receipt = self.run_checks(Path(temp), task)
                    self.assertEqual(code, 1)
                    self.assertFalse(receipt["passed"])
                    self.assertGreater(receipt["errors"] + receipt["failures"], 0)

    def test_html_smoke_detects_retained_handler(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture = '''import pathlib, re, sys
p=pathlib.Path(sys.argv[1]);s=p.read_text()
s=re.sub(r'<script>.*?</script>','',s)
s=re.sub(r' onclick="[^"]*"','',s)
p.write_text(s)
'''
            (root / "filter.py").write_text(fixture, encoding="utf8")
            self.assertEqual(self.run_checks(root, "html-js-filter")[0], 0)
            (root / "filter.py").write_text(fixture.replace("s=re.sub(r' onclick", "#s=re.sub(r' onclick"), encoding="utf8")
            code, receipt = self.run_checks(root, "html-js-filter")
            self.assertEqual(code, 1)
            self.assertEqual(receipt["failures"], 1)
            self.assertEqual(receipt["tests"], 3)

    def test_cipher_sample_smoke_detects_extra_newline_not_generalization(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data/sample_plaintext.txt").write_bytes(b"Sample.")
            (root / "data/sample_ciphertext.txt").write_bytes(b"Fkeqlr.")
            (root / "requirements.txt").write_text("", encoding="utf8")
            fixture = '''import pathlib, sys
if len(sys.argv)!=2 or not pathlib.Path(sys.argv[1]).is_file(): sys.exit(1)
sys.stdout.write("Sample.")
'''
            (root / "cracker.py").write_text(fixture, encoding="utf8")
            self.assertEqual(self.run_checks(root, "interleaved-vigenere")[0], 0)
            (root / "cracker.py").write_text(fixture.replace('"Sample."', '"Sample.\\n"'), encoding="utf8")
            code, receipt = self.run_checks(root, "interleaved-vigenere")
            self.assertEqual(code, 1)
            self.assertEqual(receipt["failures"], 1)


if __name__ == "__main__":
    unittest.main()
