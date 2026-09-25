import subprocess
import tempfile
import unittest
from pathlib import Path

from comparison_sandbox import fingerprint, collect_changes, rollback


class SandboxStateTests(unittest.TestCase):
    def fixture(self, root):
        def git(*args):
            return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL, text=True).strip()
        git("init", "-q")
        git("config", "core.autocrlf", "false")
        git("config", "core.hooksPath", "/dev/null")
        (root / ".git/tbf-owned").touch()
        (root / "app.py").write_text("def value():\n    return 1\n", encoding="utf8")
        (root / "empty").mkdir()
        git("add", "-f", "-A")
        git("-c", "user.name=test", "-c", "user.email=test@local.invalid", "commit", "-qm", "base")
        return git("rev-parse", "HEAD")

    def test_raw_source_identity_and_function_hunks_then_owned_rollback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = self.fixture(root)
            initial = fingerprint(root, base)
            (root / "app.py").write_text("def value():\n    return 2\n", encoding="utf8")
            (root / "new.txt").write_text("new", encoding="utf8")
            candidate = fingerprint(root, base)
            self.assertNotEqual(candidate["source_sha256"], initial["source_sha256"])
            change = collect_changes(root, base)
            self.assertEqual(change["functions"][0]["function"], "value")
            self.assertIn("+    return 2", change["functions"][0]["hunk"])
            self.assertTrue(change["unsupported"])
            nested = root / "nested"
            nested.mkdir()
            subprocess.run(["git", "-C", str(nested), "init", "-q"], check=True, capture_output=True)
            with self.assertRaises(subprocess.CalledProcessError):
                fingerprint(root, base)
            rollback(root, base, initial["directories"])
            self.assertEqual(fingerprint(root, base)["source_sha256"], initial["source_sha256"])
            self.assertFalse((root / "new.txt").exists())
            self.assertFalse((root / "nested").exists())
            self.assertTrue((root / "empty").is_dir())

    def test_git_ownership_and_head_are_required(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = self.fixture(root)
            with self.assertRaises(ValueError):
                fingerprint(root, "0" * 40)
            (root / ".git/tbf-owned").unlink()
            with self.assertRaises(ValueError):
                rollback(root, base, [])

    def test_module_level_change_is_not_hidden_by_empty_function_inventory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = self.fixture(root)
            (root / "app.py").write_text("LIMIT = 2\ndef value():\n    return 1\n", encoding="utf8")
            change = collect_changes(root, base)
            self.assertEqual(change["functions"], [])
            self.assertTrue(change["unsupported"])
            self.assertIn("LIMIT", change["diff"])


if __name__ == "__main__":
    unittest.main()
