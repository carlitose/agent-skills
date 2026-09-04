from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "ticket-autopilot" / "scripts" / "ticket-autopilot.py"
sys.path.insert(0, str(CLI.parent))

from autopilot.worktree_gc import (  # type: ignore[import-not-found]
    WorktreeGCError,
    classify_operational_state,
    load_owner_manifest,
)


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, text=True, capture_output=True, check=True
    ).stdout.strip()


def ticket_text() -> str:
    return """---
ticket_schema: 1
ticket_id: "GC-01"
execution_mode: AFK
blocked_by: []
---

# Garbage collection fixture
"""


class WorktreeGCTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.email", "tests@example.invalid")
        git(self.repo, "config", "user.name", "Worktree GC Tests")
        git(
            self.repo,
            "remote",
            "add",
            "origin",
            "https://github.com/example/worktree-gc-fixture.git",
        )
        tickets = self.repo / "tickets"
        tickets.mkdir()
        (tickets / "01.md").write_text(ticket_text(), encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "fixture")

    def cli(self, *args: str, check: bool = True) -> dict[str, object]:
        result = subprocess.run(
            [sys.executable, "-B", str(CLI), *args],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=False,
        )
        if check and result.returncode:
            self.fail(f"CLI failed: {result.stderr}\n{result.stdout}")
        return json.loads(result.stdout)

    def test_run_persists_exact_owner_and_plan_protects_running_run(self) -> None:
        result = self.cli(
            "run",
            str(self.repo / "tickets"),
            "--repo",
            str(self.repo),
            "--run-id",
            "gc-running",
            "--final-tree-mode",
            "off",
        )
        data = result["data"]
        owner_path = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / "gc-running"
            / "worktree-owner.json"
        )
        self.assertTrue(owner_path.is_file())
        owner = load_owner_manifest(owner_path)
        self.assertEqual("created-by-run", owner["origin"]["kind"])
        self.assertEqual(data["worktree"], owner["worktree_path"])
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), owner["base_sha"])

        planned = self.cli(
            "worktree-gc-plan",
            "--repo",
            str(self.repo),
        )["data"]
        self.assertEqual("worktree-gc-plan-v1", planned["contract_version"])
        self.assertRegex(planned["plan_sha256"], r"^[0-9a-f]{64}$")
        self.assertTrue(Path(planned["plan_path"]).is_file())
        [entry] = planned["entries"]
        self.assertEqual("protected", entry["disposition"])
        self.assertIn("run-not-completed", entry["reasons"])

        replay = self.cli(
            "worktree-gc-plan",
            "--repo",
            str(self.repo),
        )["data"]
        self.assertEqual(planned["plan_sha256"], replay["plan_sha256"])
        self.assertEqual(
            Path(planned["plan_path"]).read_bytes(),
            Path(replay["plan_path"]).read_bytes(),
        )

    def test_unsupported_remote_is_hashed_but_credentials_are_rejected(self) -> None:
        git(
            self.repo,
            "remote",
            "set-url",
            "origin",
            "https://example.invalid/repo.git",
        )
        result = self.cli(
            "run",
            str(self.repo / "tickets"),
            "--repo",
            str(self.repo),
            "--provider",
            "github",
            "--run-id",
            "gc-unsupported-remote",
            "--final-tree-mode",
            "off",
        )["data"]
        owner = load_owner_manifest(
            Path(result["ledger"]).parent / "worktree-owner.json"
        )
        self.assertEqual("local-or-unsupported", owner["provider"])
        self.assertRegex(owner["normalized_remote"], r"^sha256:[0-9a-f]{64}$")

        git(
            self.repo,
            "remote",
            "set-url",
            "origin",
            "https://secret@example.invalid/repo.git",
        )
        rejected = self.cli(
            "run",
            str(self.repo / "tickets"),
            "--repo",
            str(self.repo),
            "--provider",
            "github",
            "--run-id",
            "gc-credential-remote",
            "--final-tree-mode",
            "off",
            check=False,
        )
        self.assertFalse(rejected["ok"])
        self.assertIn("credentials or parameters", rejected["error"]["message"])

    def test_manifest_loader_rejects_unknown_fields_and_digest_tampering(self) -> None:
        self.cli(
            "run",
            str(self.repo / "tickets"),
            "--repo",
            str(self.repo),
            "--run-id",
            "gc-strict",
            "--final-tree-mode",
            "off",
        )
        owner_path = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / "gc-strict"
            / "worktree-owner.json"
        )
        document = json.loads(owner_path.read_text(encoding="utf-8"))
        document["unexpected"] = True
        owner_path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaisesRegex(WorktreeGCError, "fields"):
            load_owner_manifest(owner_path)

        del document["unexpected"]
        document["payload"]["base_sha"] = "f" * 40
        owner_path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaisesRegex(WorktreeGCError, "integrity"):
            load_owner_manifest(owner_path)

    def test_operational_state_protects_open_wiki_and_incomplete_pi_sync(self) -> None:
        ledger = {
            "run_state": "completed",
            "cleanup": None,
            "gates": {},
            "tickets": {
                "WDT-01": {
                    "state": "integrated",
                    "delivery_lineage": {"head_sha": "a" * 40},
                    "delivery": {
                        "terminal-integration": {
                            "head_sha": "a" * 40,
                            "terminal_sha": "b" * 40,
                        },
                        "wiki-sync": {
                            "result": {"status": "candidate-created"},
                            "delivery": {"status": "pr-open"},
                        },
                    },
                }
            },
            "ticket_order": ["WDT-01"],
        }
        reasons = classify_operational_state(
            ledger,
            pi_sync_states=[{"phases": ["intent-persisted"], "receipt": None}],
        )
        self.assertIn("wiki-delivery-nonterminal", reasons)
        self.assertIn("pi-sync-incomplete", reasons)

    def test_terminal_operational_state_has_no_protection_reason(self) -> None:
        head = "a" * 40
        ledger = {
            "run_state": "completed",
            "cleanup": None,
            "gates": {"gate:GC-01:test:1": {"state": "passed"}},
            "tickets": {
                "GC-01": {
                    "state": "integrated",
                    "delivery_lineage": {"head_sha": head},
                    "delivery": {
                        "terminal-integration": {
                            "head_sha": head,
                            "terminal_sha": "b" * 40,
                        }
                    },
                }
            },
            "ticket_order": ["GC-01"],
        }
        self.assertEqual([], classify_operational_state(ledger))

    def test_adoption_requires_exact_ledger_digest_and_explicit_authority(self) -> None:
        result = self.cli(
            "run",
            str(self.repo / "tickets"),
            "--repo",
            str(self.repo),
            "--run-id",
            "gc-adopt",
            "--final-tree-mode",
            "off",
        )["data"]
        owner_path = Path(result["ledger"]).parent / "worktree-owner.json"
        owner_path.unlink()
        ledger_path = Path(result["ledger"])
        ledger_sha = hashlib.sha256(ledger_path.read_bytes()).hexdigest()

        mismatch = self.cli(
            "worktree-owner-adopt",
            "gc-adopt",
            "--repo",
            str(self.repo),
            "--expected-ledger-sha256",
            "0" * 64,
            "--actor",
            "human:test",
            "--evidence",
            "test://exact-adoption",
            check=False,
        )
        self.assertFalse(mismatch["ok"])
        self.assertFalse(owner_path.exists())

        adopted = self.cli(
            "worktree-owner-adopt",
            "gc-adopt",
            "--repo",
            str(self.repo),
            "--expected-ledger-sha256",
            ledger_sha,
            "--actor",
            "human:test",
            "--evidence",
            "test://exact-adoption",
        )["data"]
        self.assertEqual("legacy-adoption", adopted["manifest"]["origin"]["kind"])
        self.assertEqual(ledger_sha, adopted["manifest"]["origin"]["ledger_sha256"])
        self.assertTrue(owner_path.is_file())
        replay = self.cli(
            "worktree-owner-adopt",
            "gc-adopt",
            "--repo",
            str(self.repo),
            "--expected-ledger-sha256",
            ledger_sha,
            "--actor",
            "human:test",
            "--evidence",
            "test://exact-adoption",
        )["data"]
        self.assertTrue(replay["replayed"])


if __name__ == "__main__":
    unittest.main()
