from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.pr_body_artifact import (
    CANONICAL_BODY_ENCODING,
    PrBodyArtifactError,
    canonical_markdown,
    persist_pr_body,
    read_pr_body,
)


class PrBodyArtifactTests(unittest.TestCase):
    def test_canonicalization_preserves_unicode_and_trailing_newline_shape(self) -> None:
        fixtures = {
            "lf": ("# Café\nbody\n", "# Café\nbody\n"),
            "crlf": ("# Café\r\nbody\r\n", "# Café\nbody\n"),
            "cr": ("# Café\rbody\r", "# Café\nbody\n"),
            "mixed": ("# Café\nbody\r\n尾\r", "# Café\nbody\n尾\n"),
            "no-trailing-newline": ("# Café\r\nbody", "# Café\nbody"),
        }
        for name, (source, expected) in fixtures.items():
            with self.subTest(name=name):
                text, encoded = canonical_markdown(source)
                self.assertEqual(expected, text)
                self.assertEqual(expected.encode("utf-8"), encoded)
        with self.assertRaisesRegex(PrBodyArtifactError, "Unicode"):
            canonical_markdown("invalid surrogate: \ud800")

    def test_persistence_is_exact_binary_content_addressed_and_replayable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            text, encoded = canonical_markdown("# Café\r\nbody\r")
            digest = hashlib.sha256(encoded).hexdigest()
            path = Path(directory) / f"{digest}.md"
            persist_pr_body(path, encoded)
            self.assertEqual(encoded, path.read_bytes())
            self.assertEqual(
                text,
                read_pr_body(
                    path,
                    recorded_sha256=digest,
                    encoding=CANONICAL_BODY_ENCODING,
                ),
            )
            persist_pr_body(path, encoded)
            with self.assertRaisesRegex(PrBodyArtifactError, "contradictory"):
                persist_pr_body(path, b"different")
            with self.assertRaisesRegex(PrBodyArtifactError, "path"):
                persist_pr_body(Path(directory) / "wrong.md", encoded)

    @unittest.skipUnless(os.name == "nt", "requires Windows newline semantics")
    def test_binary_persistence_remains_lf_on_windows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _text, encoded = canonical_markdown("# Windows\r\nbody\r\n")
            path = Path(directory) / f"{hashlib.sha256(encoded).hexdigest()}.md"
            persist_pr_body(path, encoded)
            self.assertEqual(b"# Windows\nbody\n", path.read_bytes())

    def test_only_proven_legacy_windows_expansion_is_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.md"
            original = "# Café\nbody\r\n尾\n".encode("utf-8")
            recorded = hashlib.sha256(original).hexdigest()
            windows_expanded = original.replace(b"\n", b"\r\n")
            path.write_bytes(windows_expanded)
            self.assertEqual(
                "# Café\nbody\n尾\n",
                read_pr_body(path, recorded_sha256=recorded, encoding=None),
            )

            for name, corrupt in {
                "byte": windows_expanded + b"!",
                "lone-cr": original.replace(b"\n", b"\r"),
                "invalid-utf8": b"\xff\r\n",
            }.items():
                with self.subTest(name=name):
                    path.write_bytes(corrupt)
                    with self.assertRaises(PrBodyArtifactError):
                        read_pr_body(path, recorded_sha256=recorded, encoding=None)

            path.write_bytes(windows_expanded)
            with self.assertRaises(PrBodyArtifactError):
                read_pr_body(
                    path,
                    recorded_sha256=recorded,
                    encoding=CANONICAL_BODY_ENCODING,
                )

    def test_legacy_exact_artifact_must_already_be_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.md"
            canonical = "# Café\nbody\n".encode("utf-8")
            path.write_bytes(canonical)
            self.assertEqual(
                canonical.decode("utf-8"),
                read_pr_body(
                    path,
                    recorded_sha256=hashlib.sha256(canonical).hexdigest(),
                    encoding=None,
                ),
            )
            mixed = "# Café\nbody\r\n".encode("utf-8")
            path.write_bytes(mixed)
            with self.assertRaises(PrBodyArtifactError):
                read_pr_body(
                    path,
                    recorded_sha256=hashlib.sha256(mixed).hexdigest(),
                    encoding=None,
                )


if __name__ == "__main__":
    unittest.main()
