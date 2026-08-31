from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.history_codec import decode_history
from autopilot.kernel import Kernel
from autopilot.legacy_recovery import (
    RECOVERY_LOCK_RELATIVE_PATH,
    LegacyRecoveryError,
    RetirementStore,
    active_legacy_retirement,
    apply_recovery_manifest,
    prepare_recovery_manifest,
    recovery_manifest_status,
    revoke_legacy_retirement,
)
from autopilot.ledger import AtomicLedger
from autopilot.repository_merge_authority import (
    AUTHORITY_SCOPE,
    RepositoryMergeAuthorityStore,
)
from autopilot.ticket_contract import parse_ticket_folder

CLI = SCRIPTS.parent / "scripts" / "ticket-autopilot.py"


def canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def write_envelope(path: Path, payload: dict[str, object]) -> bytes:
    body = canonical(payload)
    content = canonical(
        {
            "envelope_schema": 1,
            "integrity": hashlib.sha256(body).hexdigest(),
            "payload": payload,
        }
    ) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return content


def resign_history(document: dict[str, object]) -> None:
    previous = "0" * 64
    for event in document["history"]:
        event["previous_hash"] = previous
        event.pop("hash", None)
        event["hash"] = hashlib.sha256(canonical(event)).hexdigest()
        previous = event["hash"]


def schema_three(run_id: str, ticket_folder: Path, repo: Path) -> dict[str, object]:
    document = Kernel.new(
        run_id,
        parse_ticket_folder(ticket_folder),
        repo=str(repo),
    ).ledger
    legacy = copy.deepcopy(document)
    legacy["history"] = decode_history(legacy["history"])

    def strip(snapshot: dict[str, object]) -> None:
        snapshot["schema"] = 3
        snapshot.pop("pause", None)
        snapshot.pop("legacy_lifecycle_migration", None)
        for ticket in snapshot.get("tickets", {}).values():
            for field in (
                "disposition",
                "current_source_relative_path",
                "attempt_outcome",
                "stop_reason",
                "disposition_receipt",
            ):
                ticket.pop(field, None)

    strip(legacy)
    for event in legacy["history"]:
        strip(event["snapshot"])
    resign_history(legacy)
    return legacy


class LegacyRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "tests@example.invalid"],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Tests"], cwd=self.repo, check=True
        )
        (self.repo / "README.md").write_text("fixture\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "fixture"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )
        common_raw = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        common = Path(common_raw)
        self.common = (self.repo / common).resolve() if not common.is_absolute() else common
        self.runs = self.common / "ticket-autopilot" / "runs"
        tickets = self.root / "tickets"
        tickets.mkdir()
        (tickets / "01.md").write_text(
            "---\nticket_schema: 1\nticket_id: \"01\"\nexecution_mode: AFK\nblocked_by: []\n---\n\n# Fixture\n",
            encoding="utf-8",
        )
        self.original: dict[str, bytes] = {}
        self.original["legacy-v3"] = write_envelope(
            self.runs / "legacy-v3" / "ledger.json",
            schema_three("legacy-v3", tickets, self.repo),
        )
        self.original["legacy-v2"] = write_envelope(
            self.runs / "legacy-v2" / "ledger.json",
            {"schema": 2, "run_id": "legacy-v2", "repo": str(self.repo), "history": []},
        )
        self.original["legacy-v1"] = write_envelope(
            self.runs / "legacy-v1" / "ledger.json",
            {"schema": 1, "run_id": "legacy-v1", "repo": str(self.repo), "history": []},
        )
        self.inventory = self.root / "inventory.json"
        self.inventory.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "runs": [
                        {
                            "run_id": "legacy-v3",
                            "action": "migrate",
                            "reason": "recover exact schema-3 lifecycle",
                            "successor_run_id": None,
                        },
                        {
                            "run_id": "legacy-v2",
                            "action": "retire",
                            "reason": "terminal historical delivery",
                            "successor_run_id": None,
                        },
                        {
                            "run_id": "legacy-v1",
                            "action": "retire",
                            "reason": "superseded historical attempt",
                            "successor_run_id": "legacy-v3",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.manifest = self.root / "manifest.json"

    def prepare(self) -> dict[str, object]:
        return prepare_recovery_manifest(
            repository=self.repo,
            inventory_path=self.inventory,
            output_path=self.manifest,
        )

    def apply(self, digest: str, **items: object) -> dict[str, object]:
        return apply_recovery_manifest(
            repository=self.repo,
            manifest_path=self.manifest,
            manifest_digest=digest,
            actor="operator",
            evidence="decision://test/exact-legacy-recovery",
            **items,
        )

    def test_prepare_apply_and_replay_all_legacy_schema_families(self) -> None:
        prepared = self.prepare()
        self.assertEqual([3, 2, 1], [item["ledger_schema"] for item in prepared["actions"]])
        digest = prepared["manifest_digest"]

        applied = self.apply(digest)

        self.assertEqual({"migrated": 1, "retired": 2}, applied["summary"])
        migrated = AtomicLedger(self.runs / "legacy-v3" / "ledger.json").load()
        self.assertEqual(4, migrated["schema"])
        self.assertEqual(
            self.original["legacy-v3"] and hashlib.sha256(self.original["legacy-v3"]).hexdigest(),
            migrated["legacy_lifecycle_migration"]["input_ledger_sha256"],
        )
        self.assertEqual("operator", migrated["history"][-1]["details"]["actor"])
        for run_id in ("legacy-v2", "legacy-v1"):
            ledger = self.runs / run_id / "ledger.json"
            self.assertEqual(self.original[run_id], ledger.read_bytes())
            self.assertIsNotNone(active_legacy_retirement(self.repo, ledger))
        before = {
            path: path.read_bytes()
            for path in (
                self.runs / "legacy-v3" / "ledger.json",
                self.runs / "legacy-v2" / "legacy-retirement.json",
                self.runs / "legacy-v1" / "legacy-retirement.json",
                Path(applied["progress_path"]),
            )
        }

        replay = self.apply(digest)

        self.assertTrue(replay["intent_replayed"])
        self.assertEqual(before, {path: path.read_bytes() for path in before})
        status = recovery_manifest_status(
            repository=self.repo,
            manifest_path=self.manifest,
            manifest_digest=digest,
        )
        self.assertEqual(
            {"migrated": 1, "retired": 2, "failed": 0, "untouched": 0},
            status["summary"],
        )

    def test_manifest_digest_rejects_tampering_reordering_and_stale_input(self) -> None:
        prepared = self.prepare()
        digest = prepared["manifest_digest"]
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        manifest["actions"].reverse()
        self.manifest.write_bytes(canonical(manifest) + b"\n")
        with self.assertRaisesRegex(LegacyRecoveryError, "self-digest"):
            self.apply(digest)

        self.manifest.unlink()
        prepared = self.prepare()
        ledger = self.runs / "legacy-v2" / "ledger.json"
        ledger.write_bytes(ledger.read_bytes() + b" ")
        with self.assertRaisesRegex(LegacyRecoveryError, "input digest changed"):
            self.apply(prepared["manifest_digest"])
        intent = self.common / "ticket-autopilot" / "legacy-recovery" / "intents" / f"{prepared['manifest_digest']}.json"
        self.assertTrue(intent.is_file())
        self.assertFalse((self.runs / "legacy-v2" / "legacy-retirement.json").exists())

    def test_crash_after_migration_write_replays_without_duplicate_event(self) -> None:
        digest = self.prepare()["manifest_digest"]

        def crash(phase: str, sequence: int | None) -> None:
            if phase == "after-action-write" and sequence == 1:
                raise RuntimeError("simulated crash")

        with self.assertRaisesRegex(RuntimeError, "simulated crash"):
            self.apply(digest, crash_hook=crash)
        migrated = AtomicLedger(self.runs / "legacy-v3" / "ledger.json").load()
        history_length = len(migrated["history"])
        partial = recovery_manifest_status(
            repository=self.repo,
            manifest_path=self.manifest,
            manifest_digest=digest,
        )
        self.assertEqual(
            {"migrated": 1, "retired": 0, "failed": 0, "untouched": 2},
            partial["summary"],
        )

        self.apply(digest)

        replayed = AtomicLedger(self.runs / "legacy-v3" / "ledger.json").load()
        self.assertEqual(history_length, len(replayed["history"]))
        self.assertEqual(
            1,
            sum(event["event"] == "ledger-v3-lifecycle-migrated" for event in replayed["history"]),
        )

    def test_crash_before_first_effect_leaves_only_immutable_intent(self) -> None:
        digest = self.prepare()["manifest_digest"]

        def crash(phase: str, sequence: int | None) -> None:
            if phase == "before-action-write" and sequence == 1:
                raise RuntimeError("simulated crash")

        with self.assertRaisesRegex(RuntimeError, "simulated crash"):
            self.apply(digest, crash_hook=crash)
        for run_id, content in self.original.items():
            self.assertEqual(content, (self.runs / run_id / "ledger.json").read_bytes())
        intent = self.common / "ticket-autopilot" / "legacy-recovery" / "intents" / f"{digest}.json"
        self.assertTrue(intent.is_file())
        self.apply(digest)

    def test_crash_after_progress_write_replays_completed_prefix(self) -> None:
        digest = self.prepare()["manifest_digest"]

        def crash(phase: str, sequence: int | None) -> None:
            if phase == "after-progress-write" and sequence == 1:
                raise RuntimeError("simulated crash")

        with self.assertRaisesRegex(RuntimeError, "simulated crash"):
            self.apply(digest, crash_hook=crash)
        migrated = self.runs / "legacy-v3" / "ledger.json"
        before = migrated.read_bytes()
        self.apply(digest)
        self.assertEqual(before, migrated.read_bytes())

    def test_crash_after_retirement_write_replays_without_duplicate_event(self) -> None:
        digest = self.prepare()["manifest_digest"]

        def crash(phase: str, sequence: int | None) -> None:
            if phase == "after-action-write" and sequence == 2:
                raise RuntimeError("simulated crash")

        with self.assertRaisesRegex(RuntimeError, "simulated crash"):
            self.apply(digest, crash_hook=crash)
        sidecar = self.runs / "legacy-v2" / "legacy-retirement.json"
        before = sidecar.read_bytes()

        self.apply(digest)

        self.assertEqual(before, sidecar.read_bytes())
        state = RetirementStore(
            self.runs / "legacy-v2" / "ledger.json",
            json.loads(self.manifest.read_text())["repository_binding"],
        ).load()
        self.assertEqual(1, len(state["events"]))

    def test_stale_malformed_and_contradictory_retirements_fail_closed(self) -> None:
        digest = self.prepare()["manifest_digest"]
        self.apply(digest)
        ledger = self.runs / "legacy-v2" / "ledger.json"
        binding = json.loads(self.manifest.read_text())["repository_binding"]
        store = RetirementStore(ledger, binding)
        with self.assertRaisesRegex(LegacyRecoveryError, "contradicts"):
            store.retire(
                ledger_sha256=hashlib.sha256(self.original["legacy-v2"]).hexdigest(),
                ledger_schema=2,
                actor="another-operator",
                evidence="decision://test/contradiction",
                reason="terminal historical delivery",
                successor_run_id=None,
                manifest_digest=digest,
                action_sequence=2,
            )
        ledger.write_bytes(ledger.read_bytes() + b" ")
        with self.assertRaisesRegex(LegacyRecoveryError, "does not match"):
            active_legacy_retirement(self.repo, ledger)
        ledger.write_bytes(self.original["legacy-v2"])
        sidecar = self.runs / "legacy-v2" / "legacy-retirement.json"
        sidecar.write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(LegacyRecoveryError, "integrity envelope"):
            active_legacy_retirement(self.repo, ledger)

    def test_revocation_disables_aggregate_skip_and_old_manifest_replay(self) -> None:
        digest = self.prepare()["manifest_digest"]
        self.apply(digest)
        ledger = self.runs / "legacy-v2" / "ledger.json"

        revoked = revoke_legacy_retirement(
            repository=self.repo,
            run_id="legacy-v2",
            actor="operator",
            evidence="decision://test/revoke",
            reason="reactivate audit visibility",
        )

        self.assertEqual("revoked", revoked["status"])
        self.assertIsNone(active_legacy_retirement(self.repo, ledger))
        with self.assertRaisesRegex(LegacyRecoveryError, "does not match application intent"):
            self.apply(digest)

    def test_merge_all_reports_only_exact_active_retirement_as_retired_legacy(self) -> None:
        digest = self.prepare()["manifest_digest"]
        self.apply(digest)
        subprocess.run(
            ["git", "remote", "add", "origin", "git@github.com:example/legacy-recovery.git"],
            cwd=self.repo,
            check=True,
        )
        RepositoryMergeAuthorityStore(self.repo).grant(
            actor="operator",
            evidence="decision://test/merge-all",
            scope=AUTHORITY_SCOPE,
        )

        result = subprocess.run(
            [sys.executable, "-B", str(CLI), "merge-all", "--repo", str(self.repo)],
            text=True,
            capture_output=True,
            check=True,
        )
        runs = json.loads(result.stdout)["data"]["runs"]
        by_id = {item["run_id"]: item for item in runs}
        self.assertEqual("retired-legacy", by_id["legacy-v1"]["result"])
        self.assertEqual("retired-legacy", by_id["legacy-v2"]["result"])
        self.assertNotEqual("retired-legacy", by_id["legacy-v3"]["result"])

    def test_single_run_migration_command_uses_the_same_persisted_manifest_intent(self) -> None:
        inventory = json.loads(self.inventory.read_text(encoding="utf-8"))
        inventory["runs"] = inventory["runs"][:1]
        self.inventory.write_text(json.dumps(inventory), encoding="utf-8")
        digest = self.prepare()["manifest_digest"]

        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(CLI),
                "migrate-run-lifecycle",
                "legacy-v3",
                "--repo",
                str(self.repo),
                "--manifest",
                str(self.manifest),
                "--manifest-sha256",
                digest,
                "--actor",
                "operator",
                "--evidence",
                "decision://test/exact-legacy-recovery",
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        data = json.loads(result.stdout)["data"]
        self.assertEqual(4, data["migrated_schema"])
        self.assertTrue(Path(data["application"]["intent_path"]).is_file())

    def test_application_fails_closed_when_repository_recovery_lock_is_held(self) -> None:
        digest = self.prepare()["manifest_digest"]
        lock = self.common / RECOVERY_LOCK_RELATIVE_PATH
        lock.parent.mkdir(parents=True, exist_ok=True)
        with lock.open("a+", encoding="ascii") as handle:
            from autopilot.file_lock import acquire_file_lock, release_file_lock

            acquire_file_lock(handle, blocking=False)
            try:
                with self.assertRaisesRegex(LegacyRecoveryError, "application is locked"):
                    self.apply(digest)
            finally:
                release_file_lock(handle)


if __name__ == "__main__":
    unittest.main()
