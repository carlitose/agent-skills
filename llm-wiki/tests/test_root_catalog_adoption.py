from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
REPO_ROOT = SKILL_ROOT.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from root_catalog import (  # noqa: E402
    OWNERS,
    CatalogAdoptionSpan,
    CatalogOwnershipError,
    adopt_catalog_bytes,
    adopt_catalog_file,
    parse_catalog,
    remove_catalog_markers,
)

LEGACY_FIXTURE = Path(__file__).parent / "fixtures" / "agent-skills-legacy-index.md"
LEGACY_SHA256 = "7c0757c44e53e7627dc4b2df4e3bda798cb522c5d4e15345a90f5630f0b13e5f"
ADOPTED_SHA256 = "340fbde7a36da7e9a5800c2f70a5724e413debbd9a271efe094bea5ba899199f"
LEGACY_SPANS = (
    CatalogAdoptionSpan("project-sources", 0, 23498),
    CatalogAdoptionSpan("session-sources", 23498, 48479),
    CatalogAdoptionSpan("timeline", 48479, 48573),
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sample() -> tuple[bytes, tuple[CatalogAdoptionSpan, ...]]:
    parts = (
        "# Índice\r\n\r\n## Project source\r\n- café\r\n\r\n".encode(),
        "## Session sources\n- session\n\n".encode(),
        "## Timeline\r\n- event\r\n".encode(),
    )
    first = len(parts[0])
    second = first + len(parts[1])
    return b"".join(parts), (
        CatalogAdoptionSpan(OWNERS[0], 0, first),
        CatalogAdoptionSpan(OWNERS[1], first, second),
        CatalogAdoptionSpan(OWNERS[2], second, sum(map(len, parts))),
    )


class CatalogAdoptionBytesTests(unittest.TestCase):
    def test_adoption_is_lossless_parseable_and_byte_idempotent(self) -> None:
        legacy, spans = sample()

        adopted = adopt_catalog_bytes(legacy, digest(legacy), spans)

        self.assertEqual(6, adopted.count(b"<!-- llm-wiki:catalog:"))
        self.assertEqual(legacy, remove_catalog_markers(adopted))
        self.assertEqual(set(OWNERS), set(parse_catalog(adopted.decode("utf-8"))))
        self.assertEqual(adopted, adopt_catalog_bytes(adopted, digest(legacy), spans))

    def test_exact_agent_skills_legacy_fixture_has_the_frozen_digest_and_map(self) -> None:
        legacy = LEGACY_FIXTURE.read_bytes()

        adopted = adopt_catalog_bytes(legacy, LEGACY_SHA256, LEGACY_SPANS)

        self.assertEqual(LEGACY_SHA256, digest(remove_catalog_markers(adopted)))
        self.assertEqual(ADOPTED_SHA256, digest(adopted))
        self.assertEqual(set(OWNERS), set(parse_catalog(adopted.decode("utf-8"))))
        self.assertEqual(adopted, adopt_catalog_bytes(adopted, LEGACY_SHA256, LEGACY_SPANS))

    def test_digest_map_encoding_and_existing_marker_failures_precede_mutation(self) -> None:
        legacy, spans = sample()
        malformed_marker = legacy + b"<!-- llm-wiki:catalog start timeline -->\n"
        cases = {
            "wrong-digest": (legacy, "0" * 64, spans),
            "missing-owner": (legacy, digest(legacy), spans[:2]),
            "unknown-owner": (
                legacy,
                digest(legacy),
                (CatalogAdoptionSpan("unknown", 0, spans[0].end), *spans[1:]),
            ),
            "duplicate-owner": (
                legacy,
                digest(legacy),
                (spans[0], CatalogAdoptionSpan(OWNERS[0], spans[1].start, spans[1].end), spans[2]),
            ),
            "wrong-order": (legacy, digest(legacy), (spans[1], spans[0], spans[2])),
            "overlap": (
                legacy,
                digest(legacy),
                (
                    spans[0],
                    CatalogAdoptionSpan(OWNERS[1], spans[0].end - 1, spans[1].end),
                    spans[2],
                ),
            ),
            "gap-in-line": (
                legacy,
                digest(legacy),
                (
                    CatalogAdoptionSpan(OWNERS[0], 0, spans[0].end - 1),
                    spans[1],
                    spans[2],
                ),
            ),
            "non-integer-offset": (
                legacy,
                digest(legacy),
                (CatalogAdoptionSpan(OWNERS[0], "0", spans[0].end), *spans[1:]),
            ),
            "boolean-offset": (
                legacy,
                digest(legacy),
                (CatalogAdoptionSpan(OWNERS[0], False, spans[0].end), *spans[1:]),
            ),
            "out-of-range": (
                legacy,
                digest(legacy),
                (*spans[:2], CatalogAdoptionSpan(OWNERS[2], spans[2].start, len(legacy) + 1)),
            ),
            "invalid-utf8": (b"\xff", digest(b"\xff"), spans),
            "malformed-marker": (
                malformed_marker,
                digest(malformed_marker),
                spans,
            ),
        }
        for label, arguments in cases.items():
            with self.subTest(label=label), self.assertRaises(CatalogOwnershipError):
                adopt_catalog_bytes(*arguments)

    def test_an_adopted_catalog_rejects_a_contradictory_map(self) -> None:
        legacy, spans = sample()
        adopted = adopt_catalog_bytes(legacy, digest(legacy), spans)
        contradictory = (
            CatalogAdoptionSpan(OWNERS[0], 0, spans[0].end),
            CatalogAdoptionSpan(OWNERS[1], spans[1].start, spans[1].end - 1),
            spans[2],
        )

        with self.assertRaises(CatalogOwnershipError):
            adopt_catalog_bytes(adopted, digest(legacy), contradictory)


class CatalogAdoptionFileTests(unittest.TestCase):
    def test_file_adoption_is_atomic_mode_preserving_and_replay_writes_nothing(self) -> None:
        legacy, spans = sample()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "index.md"
            path.write_bytes(legacy)
            path.chmod(0o640)

            adopted = adopt_catalog_file(path, digest(legacy), spans)
            first_bytes = path.read_bytes()
            first_mtime = path.stat().st_mtime_ns
            replay = adopt_catalog_file(path, digest(legacy), spans)

            self.assertEqual("adopted", adopted["status"])
            self.assertEqual("unchanged", replay["status"])
            self.assertEqual(0o640, path.stat().st_mode & 0o777)
            self.assertEqual(first_bytes, path.read_bytes())
            self.assertEqual(first_mtime, path.stat().st_mtime_ns)

    def test_invalid_digest_and_special_paths_leave_source_untouched(self) -> None:
        legacy, spans = sample()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "index.md"
            path.write_bytes(legacy)
            before = (path.read_bytes(), path.stat().st_mtime_ns)
            with self.assertRaises(CatalogOwnershipError):
                adopt_catalog_file(path, "0" * 64, spans)
            self.assertEqual(before, (path.read_bytes(), path.stat().st_mtime_ns))
            with patch("root_catalog.os.open", side_effect=PermissionError("denied")):
                with self.assertRaises(CatalogOwnershipError):
                    adopt_catalog_file(path, digest(legacy), spans)
            self.assertEqual(before, (path.read_bytes(), path.stat().st_mtime_ns))

            directory = root / "directory"
            directory.mkdir()
            link = root / "link.md"
            link.symlink_to(path)
            special = [directory, link]
            if hasattr(os, "mkfifo"):
                fifo = root / "fifo"
                os.mkfifo(fifo)
                special.append(fifo)
            for candidate in special:
                with self.subTest(path=candidate), self.assertRaises(CatalogOwnershipError):
                    adopt_catalog_file(candidate, digest(legacy), spans)

    def test_cli_accepts_only_the_complete_explicit_map_and_replays(self) -> None:
        legacy, spans = sample()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "index.md"
            path.write_bytes(legacy)
            command = [
                sys.executable,
                "-B",
                str(SCRIPTS / "adopt_root_catalog.py"),
                str(path),
                "--expected-sha256",
                digest(legacy),
                "--json",
            ]
            for span in spans:
                command += ["--span", f"{span.owner}:{span.start}:{span.end}"]

            first = subprocess.run(command, text=True, capture_output=True, check=True)
            replay = subprocess.run(command, text=True, capture_output=True, check=True)

        self.assertEqual("adopted", json.loads(first.stdout)["status"])
        self.assertEqual("unchanged", json.loads(replay.stdout)["status"])


if __name__ == "__main__":
    unittest.main()
