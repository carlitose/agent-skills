"""Frozen extension relocation through the owning runner, without real model calls."""
import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import runner
from test_runner import Fixture, fake_pi_config, isolate_skills


class ExtensionRelocationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="dbench-relocation-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        isolate_skills(self, self.root)
        config = fake_pi_config(self.root / "config")
        self.source = config / runner.TOOL_PROFILE[0]
        (self.source.parent / "runtime.ts").write_text("export const value = 1;\n")
        self.fx = Fixture(self.root, arms=("bare", "pi-tools", "pi-full"), pi_config_root=config)
        self.snapshot = self.root / "pinned" / self.source.parent.name / self.source.name
        shutil.copytree(self.source.parent, self.snapshot.parent)
        self.manifest = self.fx.lot / "lot.json"
        self.original = self.manifest.read_bytes()
        self.sidecar = self.fx.lot / "extension-relocations.json"

    def drift(self):
        self.source.write_text("export default function updated() {}\n")

    def relocate(self, **kwargs):
        return runner.relocate_extension(self.fx.lot, kwargs.get("source", self.source),
                                         kwargs.get("snapshot", self.snapshot), kwargs.get("reason", "isolated recovery"))

    def test_same_bytes_recover_every_shared_binding_and_continue_without_replay(self):
        first = self.fx.run("toy.pi-tools.r1", 1)["requests"][0]
        self.drift()
        with self.assertRaises(runner.LotError):
            runner.load_lot(self.fx.lot)
        result = self.relocate()
        self.assertTrue(result["changed"])
        lot = runner.load_lot(self.fx.lot)
        for arm in ("pi-tools", "pi-full"):
            self.assertEqual(lot["arm_extensions"][arm][0]["path"], str(self.snapshot.resolve()))
        self.assertEqual(lot["arm_extensions"]["bare"], [])
        second = self.fx.run("toy.pi-tools.r1", 2)
        self.assertEqual(second["requests"][0], first)
        actual = second["requests"][1]["attempts"][0]["arm_extensions"][0]
        self.assertEqual(actual["path"], str(self.snapshot.resolve()))
        self.assertEqual(len(self.fx.calls()), 2)
        self.assertEqual(self.manifest.read_bytes(), self.original)
        self.assertIn("updated", self.source.read_text())
        events = [json.loads(line) for line in (self.fx.lot / "ledger.jsonl").read_text().splitlines()]
        phases = [e["phase"] for e in events if e["event"] == "relocate-extension"]
        self.assertEqual(phases, ["prepared", "applied"])

    def test_same_parent_digest_does_not_allow_another_entrypoint(self):
        with self.assertRaisesRegex(ValueError, "name"):
            self.relocate(snapshot=self.snapshot.parent / "runtime.ts")
        self.assertFalse(self.sidecar.exists())

    def test_wrong_content_unknown_binding_and_blank_reason_leave_state_unchanged(self):
        ledger = self.fx.lot / "ledger.jsonl"
        before = ledger.read_bytes() if ledger.exists() else None
        for kwargs in ({"source": self.root / "unknown.ts"}, {"reason": " "}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.relocate(**kwargs)
        self.snapshot.write_text("not the frozen source")
        with self.assertRaisesRegex(runner.LotError, "changed or disappeared"):
            self.relocate()
        self.assertEqual(self.manifest.read_bytes(), self.original)
        self.assertEqual(ledger.read_bytes() if ledger.exists() else None, before)
        self.assertFalse(self.sidecar.exists())

    def test_missing_original_entrypoint_is_recoverable(self):
        self.source.unlink()
        self.relocate()
        runner.load_lot(self.fx.lot)
        self.assertFalse(self.source.exists())

    def test_live_cell_blocks_publication(self):
        lock = self.fx.lot / "cells/toy.pi-tools.r1/lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text(str(os.getpid()))
        with mock.patch.object(runner, "_alive", return_value=True), self.assertRaisesRegex(runner.LotError, "running"):
            self.relocate()
        self.assertFalse(self.sidecar.exists())

    def test_changed_authority_blocks_publication(self):
        self.fx.authority.write_text("changed")
        with self.assertRaisesRegex(runner.LotError, "authority"):
            self.relocate()
        self.assertFalse(self.sidecar.exists())

    def test_noop_preserves_history_and_authority_provenance(self):
        self.drift()
        self.relocate()
        sidecar = self.sidecar.read_bytes()
        ledger = (self.fx.lot / "ledger.jsonl").read_bytes()
        result = self.relocate(reason="different caller wording")
        self.assertFalse(result["changed"])
        self.assertEqual(self.sidecar.read_bytes(), sidecar)
        self.assertEqual((self.fx.lot / "ledger.jsonl").read_bytes(), ledger)

    def test_only_latest_snapshot_is_required_but_history_is_kept(self):
        self.drift()
        self.relocate()
        other = self.root / "pinned2" / self.source.parent.name / self.source.name
        shutil.copytree(self.snapshot.parent, other.parent)
        self.relocate(snapshot=other)
        self.snapshot.unlink()
        lot = runner.load_lot(self.fx.lot)
        self.assertEqual(lot["arm_extensions"]["pi-tools"][0]["path"], str(other.resolve()))
        self.assertEqual(len(json.loads(self.sidecar.read_text())["entries"]), 2)

    def test_target_drift_is_still_blocked_after_relocation(self):
        self.relocate()
        self.snapshot.write_text("changed after publication")
        with self.assertRaisesRegex(runner.LotError, "changed or disappeared"):
            runner.load_lot(self.fx.lot)

    def test_malformed_stale_or_forged_metadata_cannot_override_the_binding(self):
        self.relocate()
        original = json.loads(self.sidecar.read_text())
        cases = [{"schema": 9}, {**original, "lot_sha256": "0" * 64},
                 {**original, "authority_sha256": "0" * 64}, {**original, "unexpected": True},
                 {**original, "entries": [{**original["entries"][0], "sha256": "0" * 64}]}]
        for document in cases:
            with self.subTest(document=document):
                self.sidecar.write_text(json.dumps(document))
                with self.assertRaises(ValueError):
                    runner.load_lot(self.fx.lot)
        self.sidecar.write_text("{truncated")
        with self.assertRaises(ValueError):
            runner.load_lot(self.fx.lot)

    def test_manifest_change_cannot_silently_reuse_old_relocation_metadata(self):
        self.relocate()
        self.manifest.write_bytes(self.original + b"\n")
        with self.assertRaisesRegex(ValueError, "manifest"):
            runner.load_lot(self.fx.lot)

    def test_failed_publication_leaves_a_prepared_receipt_and_no_active_override(self):
        self.drift()
        with mock.patch.object(runner, "dump", side_effect=OSError("disk full")), self.assertRaises(OSError):
            self.relocate()
        self.assertFalse(self.sidecar.exists())
        self.assertEqual(self.manifest.read_bytes(), self.original)
        last = json.loads((self.fx.lot / "ledger.jsonl").read_text().splitlines()[-1])
        self.assertEqual((last["event"], last["phase"]), ("relocate-extension", "prepared"))
        with self.assertRaises(runner.LotError):
            runner.load_lot(self.fx.lot)

    def test_cli_uses_the_same_supported_operation(self):
        self.drift()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exit_code = runner.main(["relocate-extension", "--lot", str(self.fx.lot),
                                    "--source", str(self.source), "--snapshot", str(self.snapshot),
                                    "--reason", "CLI recovery"])
        self.assertEqual(exit_code, 0)
        self.assertTrue(json.loads(out.getvalue())["changed"])
        runner.load_lot(self.fx.lot)


if __name__ == "__main__":
    unittest.main()
