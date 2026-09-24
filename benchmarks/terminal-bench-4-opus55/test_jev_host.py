"""Host-only Jev key handling; every credential here is a synthetic fixture."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ticket-driver" / "scripts"))
from jev_host import JevKeyError, jev_key_scope, read_jev_key


FIXTURE = "synthetic-credential-not-valid"


class JevHostTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "jev.env"

    def test_single_raw_token_and_env_assignment_are_supported(self):
        for content in (FIXTURE + "\n", "TYPESAFE_API_KEY=" + FIXTURE + "\n"):
            with self.subTest(form=content.startswith("TYPESAFE_API_KEY=")):
                self.path.write_text(content, encoding="utf-8")
                self.assertEqual(read_jev_key(self.path), FIXTURE)

    def test_bad_or_ambiguous_file_fails_closed(self):
        for content in ("", "OTHER_KEY=" + FIXTURE, "TYPESAFE_API_KEY=\n",
                        FIXTURE + "\n" + FIXTURE, "C:/Users/path", "not a token"):
            with self.subTest(kind=content[:4]):
                self.path.write_text(content, encoding="utf-8")
                with self.assertRaises(JevKeyError):
                    read_jev_key(self.path)

    def test_scoped_key_is_not_visible_to_a_real_child_and_is_removed_after_exit(self):
        from arbiter import isolated_key  # local ticket-driver scripts, imported by test runner path
        self.path.write_text(FIXTURE, encoding="utf-8")
        self.assertNotIn("TYPESAFE_API_KEY", os.environ)
        with jev_key_scope(self.path, isolated_key):
            self.assertNotIn("TYPESAFE_API_KEY", os.environ)
            result = subprocess.run([sys.executable, "-B", "-c",
                                     "import os; print('TYPESAFE_API_KEY' in os.environ)"],
                                    text=True, capture_output=True, check=True, timeout=10)
            self.assertEqual(result.stdout.strip(), "False")
        self.assertNotIn("TYPESAFE_API_KEY", os.environ)

    def test_preexisting_credential_is_never_overridden(self):
        from arbiter import isolated_key
        self.path.write_text(FIXTURE, encoding="utf-8")
        prior = os.environ.get("TYPESAFE_API_KEY")
        os.environ["TYPESAFE_API_KEY"] = "other-synthetic-credential"
        try:
            with self.assertRaises(JevKeyError):
                with jev_key_scope(self.path, isolated_key):
                    pass
            self.assertEqual(os.environ["TYPESAFE_API_KEY"], "other-synthetic-credential")
        finally:
            if prior is None:
                os.environ.pop("TYPESAFE_API_KEY", None)
            else:
                os.environ["TYPESAFE_API_KEY"] = prior


if __name__ == "__main__":
    unittest.main()
