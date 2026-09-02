from __future__ import annotations

import copy
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "ticket-autopilot" / "scripts" / "ticket-autopilot.py"
sys.path.insert(0, str(CLI.parent))

from autopilot.final_tree_projection import (
    canonical_bytes,
    plan_tracked_completion,
    projection_config,
)
from autopilot.final_tree_transaction import (
    FinalTreeTransactionError,
    apply_projection_transaction,
    new_projection_transaction,
    projection_transaction_reference,
    record_effect_readback,
    record_effect_started,
    record_effects_checkpoint,
    record_final_tree_checkpoint,
    validate_projection_transaction,
)
from autopilot.ticket_contract import ticket_source_digest


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


class TransactionHarness:
    def __init__(self, root: Path):
        self.repo = root / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.email", "tests@example.invalid")
        git(self.repo, "config", "user.name", "Transaction Tests")
        source = self.repo / "docs/tickets/feature/02.md"
        source.parent.mkdir(parents=True)
        source.write_text("# Ticket\n\nExact bytes.\n", encoding="utf-8")
        spec = self.repo / "docs/specs/map.md"
        spec.parent.mkdir(parents=True)
        spec.write_text(
            "[Ticket](../tickets/feature/02.md#acceptance)\n",
            encoding="utf-8",
        )
        implementation = self.repo / "implementation.txt"
        implementation.write_text("before\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "base")
        base_tree = git(self.repo, "rev-parse", "HEAD^{tree}")
        implementation.write_text("after\n", encoding="utf-8")
        git(self.repo, "add", "implementation.txt")
        implementation_tree = git(self.repo, "write-tree")
        candidate = {
            "contract_version": 2,
            "base_tree_oid": base_tree,
            "candidate_tree_oid": implementation_tree,
            "ticket_digest": ticket_source_digest(source),
        }
        summary = {
            "schema": 1,
            "run_id": "projection-transaction-run",
            "ticket_id": "FTV-02",
            "implementation_status": "complete",
            "candidate_ref": candidate,
            "ticket_source_mode": "tracked",
            "snapshot_manifest_digest": "a" * 64,
        }
        planned = plan_tracked_completion(
            self.repo,
            run_id="projection-transaction-run",
            ticket_id="FTV-02",
            artifact_generation=0,
            configuration=projection_config("enabled"),
            candidate_ref=candidate,
            source_relative_path="docs/tickets/feature/02.md",
            destination_relative_path="docs/tickets/feature/done/02.md",
            receipt_document=summary,
            source_mode="tracked",
            delivery_metadata={"branch": {"branch": "ticket/FTV-02"}},
        )
        self.manifest = planned.manifest
        reference = projection_transaction_reference(
            self.manifest,
            artifact="/immutable/final-tree-manifest.json",
            sha256=hashlib.sha256(planned.bytes).hexdigest(),
        )
        self.transaction = new_projection_transaction(
            reference, self.manifest
        )

    def persist_effect_started(self, effect_key: str) -> None:
        self.transaction, _changed = record_effect_started(
            self.transaction, effect_key
        )

    def persist_effect(
        self, effect_key: str, readback: dict[str, Any]
    ) -> None:
        self.transaction, _changed = record_effect_readback(
            self.transaction, effect_key, readback
        )

    def persist_readback(
        self, actual_tree_oid: str, actual_diff_digest: str
    ) -> None:
        self.transaction, _changed = record_effects_checkpoint(
            self.transaction,
            actual_tree_oid=actual_tree_oid,
            actual_diff_digest=actual_diff_digest,
        )

    def apply(self, **kwargs: Any) -> dict[str, Any]:
        return apply_projection_transaction(
            self.repo,
            self.manifest,
            get_transaction=lambda: self.transaction,
            persist_effect_started=self.persist_effect_started,
            persist_effect=self.persist_effect,
            persist_effects_readback=self.persist_readback,
            **kwargs,
        )

    def bind_final(self) -> None:
        self.transaction, _changed = record_final_tree_checkpoint(
            self.transaction,
            self.manifest["planned_delivery_candidate_ref"],
        )


class FinalTreeTransactionTests(unittest.TestCase):
    def harness(self) -> TransactionHarness:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        return TransactionHarness(Path(temporary.name))

    def test_applies_exact_effects_checkpoints_and_closed_replay(self) -> None:
        harness = self.harness()
        self.assertEqual("intent-persisted", harness.transaction["status"])
        result = harness.apply()
        self.assertEqual("applied", result["result"])
        self.assertEqual(
            harness.manifest["planned_delivery_candidate_ref"],
            result["candidate_ref"],
        )
        self.assertEqual("effects-read-back", harness.transaction["status"])
        harness.bind_final()
        self.assertEqual(
            "projected-not-integrated", harness.transaction["status"]
        )
        replay = harness.apply()
        self.assertEqual("already-applied", replay["result"])
        self.assertEqual(
            harness.transaction,
            validate_projection_transaction(harness.transaction),
        )
        self.assertEqual(
            harness.manifest["planned_delivery_candidate_ref"][
                "candidate_tree_oid"
            ],
            git(harness.repo, "write-tree"),
        )
        self.assertEqual("", git(harness.repo, "diff", "--name-only"))
        self.assertEqual(
            "",
            git(
                harness.repo,
                "ls-files",
                "--others",
                "--exclude-standard",
            ),
        )

    def test_resumes_after_intent_and_every_unrecorded_repository_effect(self) -> None:
        probe = self.harness()
        effect_keys = [
            effect["effect_key"] for effect in probe.manifest["effects"]
        ]
        for crash_key in effect_keys:
            with self.subTest(effect_key=crash_key):
                harness = self.harness()

                def crash(effect_key: str) -> None:
                    if effect_key == crash_key:
                        raise RuntimeError("simulated crash")

                with self.assertRaisesRegex(RuntimeError, "simulated crash"):
                    harness.apply(after_repository_effect=crash)
                resumed = harness.apply()
                self.assertEqual("applied", resumed["result"])
                self.assertEqual(
                    len(harness.manifest["effects"]),
                    len(harness.transaction["effects_applied"]),
                )

    def test_resumes_after_each_persisted_effect_and_effects_readback(self) -> None:
        effect_count = len(self.harness().manifest["effects"])
        for crash_after in range(1, effect_count + 1):
            with self.subTest(crash_after=crash_after):
                harness = self.harness()
                original = harness.persist_effect
                persisted = 0

                def persist_then_crash(
                    effect_key: str, readback: dict[str, Any]
                ) -> None:
                    nonlocal persisted
                    original(effect_key, readback)
                    persisted += 1
                    if persisted == crash_after:
                        raise RuntimeError("simulated persisted-effect crash")

                with self.assertRaisesRegex(
                    RuntimeError, "persisted-effect crash"
                ):
                    apply_projection_transaction(
                        harness.repo,
                        harness.manifest,
                        get_transaction=lambda: harness.transaction,
                        persist_effect_started=harness.persist_effect_started,
                        persist_effect=persist_then_crash,
                        persist_effects_readback=harness.persist_readback,
                    )
                harness.apply()
                self.assertEqual(
                    "effects-read-back", harness.transaction["status"]
                )

        harness = self.harness()
        original_readback = harness.persist_readback

        def readback_then_crash(tree_oid: str, diff_digest: str) -> None:
            original_readback(tree_oid, diff_digest)
            raise RuntimeError("simulated readback crash")

        with self.assertRaisesRegex(RuntimeError, "readback crash"):
            apply_projection_transaction(
                harness.repo,
                harness.manifest,
                get_transaction=lambda: harness.transaction,
                persist_effect_started=harness.persist_effect_started,
                persist_effect=harness.persist_effect,
                persist_effects_readback=readback_then_crash,
            )
        self.assertEqual("effects-read-back", harness.transaction["status"])
        harness.apply()
        harness.bind_final()
        self.assertEqual(
            "projected-not-integrated", harness.transaction["status"]
        )

    def test_contradictions_block_without_publishing_or_rolling_back(self) -> None:
        harness = self.harness()
        source = harness.repo / "docs/tickets/feature/02.md"
        destination = harness.repo / "docs/tickets/feature/done/02.md"
        destination.parent.mkdir()
        destination.write_bytes(source.read_bytes())
        with self.assertRaisesRegex(
            FinalTreeTransactionError, "both source and destination"
        ):
            harness.apply()
        self.assertEqual("intent-persisted", harness.transaction["status"])
        self.assertTrue(source.exists())
        self.assertTrue(destination.exists())

        harness = self.harness()
        (harness.repo / "docs/tickets/feature/02.md").unlink()
        with self.assertRaisesRegex(
            FinalTreeTransactionError, "both source and destination absent"
        ):
            harness.apply()
        self.assertEqual("intent-persisted", harness.transaction["status"])

        harness = self.harness()
        link = harness.repo / "docs/specs/map.md"
        link.write_text("contradictory\n", encoding="utf-8")
        git(harness.repo, "add", "docs/specs/map.md")
        with self.assertRaisesRegex(
            FinalTreeTransactionError, "index differs"
        ):
            harness.apply()
        self.assertEqual("intent-persisted", harness.transaction["status"])
        self.assertIsNone(
            harness.transaction["checkpoints"]["final-tree-bound"]
        )

        harness = self.harness()
        receipt = (
            harness.repo
            / "docs/tickets/feature/done/02.completion.json"
        )
        receipt.parent.mkdir()
        receipt.write_bytes(b"contradictory receipt\n")
        with self.assertRaisesRegex(
            FinalTreeTransactionError, "unexpected untracked"
        ):
            harness.apply()
        self.assertEqual(b"contradictory receipt\n", receipt.read_bytes())
        self.assertIsNone(
            harness.transaction["checkpoints"]["final-tree-bound"]
        )

    def test_stale_candidate_mode_and_unexpected_index_rows_block_before_effects(self) -> None:
        cases = ("candidate", "mode", "unexpected-row")
        for case in cases:
            with self.subTest(case=case):
                harness = self.harness()
                if case == "candidate":
                    (harness.repo / "implementation.txt").write_text(
                        "stale candidate\n", encoding="utf-8"
                    )
                    git(harness.repo, "add", "implementation.txt")
                elif case == "mode":
                    source = harness.repo / "docs/tickets/feature/02.md"
                    source.chmod(0o755)
                    git(harness.repo, "add", "docs/tickets/feature/02.md")
                else:
                    (harness.repo / "unexpected.txt").write_text(
                        "unexpected\n", encoding="utf-8"
                    )
                    git(harness.repo, "add", "unexpected.txt")
                with self.assertRaisesRegex(
                    FinalTreeTransactionError, "index differs"
                ):
                    harness.apply()
                self.assertEqual(
                    "intent-persisted", harness.transaction["status"]
                )
                self.assertEqual([], harness.transaction["effects_applied"])
                self.assertIsNone(harness.transaction["active_effect"])

    def test_transaction_identity_effect_order_and_final_binding_are_immutable(self) -> None:
        harness = self.harness()
        self.assertEqual(
            harness.manifest["effects"],
            harness.transaction["effect_bindings"],
        )

        tampered_binding = copy.deepcopy(harness.transaction)
        tampered_binding["effect_bindings"][0]["path"] = "docs/specs/other.md"
        with self.assertRaisesRegex(
            FinalTreeTransactionError, "effect bindings"
        ):
            validate_projection_transaction(tampered_binding)

        duplicate = copy.deepcopy(harness.transaction)
        duplicate["effect_bindings"].append(
            copy.deepcopy(duplicate["effect_bindings"][0])
        )
        with self.assertRaisesRegex(
            FinalTreeTransactionError, "bindings"
        ):
            validate_projection_transaction(duplicate)

        tampered = copy.deepcopy(harness.transaction)
        tampered["checkpoints"]["intent-persisted"][
            "checkpoint_key"
        ] = "0" * 64
        with self.assertRaisesRegex(
            FinalTreeTransactionError, "intent identity"
        ):
            validate_projection_transaction(tampered)

        wrong_contract = copy.deepcopy(harness.transaction)
        wrong_contract["contract_version"] = 2
        with self.assertRaisesRegex(
            FinalTreeTransactionError, "identity"
        ):
            validate_projection_transaction(wrong_contract)

        with self.assertRaisesRegex(
            FinalTreeTransactionError, "order"
        ):
            record_effect_readback(
                harness.transaction,
                harness.transaction["effect_bindings"][1]["effect_key"],
                {
                    "path": "wrong",
                    "mode": "000000",
                    "oid": "0" * 40,
                    "index_tree_oid": "a" * 40,
                    "worktree_sha256": None,
                },
            )
        harness.apply()
        contradictory = copy.deepcopy(
            harness.manifest["planned_delivery_candidate_ref"]
        )
        contradictory["candidate_tree_oid"] = "b" * 40
        with self.assertRaisesRegex(
            FinalTreeTransactionError, "binding"
        ):
            record_final_tree_checkpoint(
                harness.transaction, contradictory
            )


if __name__ == "__main__":
    unittest.main()
