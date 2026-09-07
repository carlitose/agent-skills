from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ticket-autopilot/scripts"))

from autopilot.final_tree_projection import (
    FinalTreeProjectionError,
    ProjectionExcluded,
    canonical_bytes,
    canonical_digest,
    compare_projection,
    plan_tracked_completion,
    projection_config,
    validate_manifest,
)
from autopilot.final_tree_transaction import (
    apply_projection_transaction,
    new_projection_transaction,
    projection_transaction_reference,
    record_effect_readback,
    record_effect_started,
    record_effects_checkpoint,
    record_final_tree_checkpoint,
)
from autopilot.ticket_contract import ticket_source_digest


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, check=True, timeout=30
    ).stdout


class PortableFinalTreePathTests(unittest.TestCase):
    def test_nested_completion_plans_applies_and_replays_with_real_git(self) -> None:
        for relative in (
            "docs/tickets/feature/nested/01.md",
            "docs/tickets/Spazio café/più profondo/02 résumé.md",
        ):
            with self.subTest(source=relative), tempfile.TemporaryDirectory(
                prefix="apm02-"
            ) as temporary:
                root = Path(temporary)
                repo = root / "repo"
                repo.mkdir()
                git(repo, "init", "-b", "main")
                # Configure only this new fixture; existing EOL fixtures belong to APM-03.
                for key, value in (
                    ("user.name", "Portable Path Tests"),
                    ("user.email", "tests@example.invalid"),
                    ("core.autocrlf", "false"),
                    ("core.eol", "lf"),
                    ("commit.gpgsign", "false"),
                ):
                    git(repo, "config", key, value)
                source = repo / relative
                source.parent.mkdir(parents=True)
                payload = "# Ticket\n\nExact UTF-8: lógica.\n".encode("utf-8")
                source.write_bytes(payload)
                spec = repo / "docs/specs/map.md"
                spec.parent.mkdir(parents=True)
                target = "../" + relative.removeprefix("docs/")
                # Match the existing literal-path link contract, not URI decoding.
                spec.write_bytes(f"[Ticket]({target}#acceptance)\n".encode("utf-8"))
                git(repo, "add", ".")
                git(repo, "commit", "-m", "base")
                base = git(repo, "write-tree").decode().strip()
                (repo / "implementation.txt").write_bytes(b"implementation\n")
                git(repo, "add", "implementation.txt")
                tree = git(repo, "write-tree").decode().strip()
                candidate = {
                    "contract_version": 2,
                    "base_tree_oid": base,
                    "candidate_tree_oid": tree,
                    "ticket_digest": ticket_source_digest(source),
                }
                receipt = {
                    "schema": 1,
                    "run_id": "portable-path-run",
                    "ticket_id": "APM-02",
                    "implementation_status": "complete",
                    "candidate_ref": candidate,
                    "ticket_source_mode": "tracked",
                    "snapshot_manifest_digest": "a" * 64,
                }
                destination = source.parent.relative_to(repo).as_posix() + "/done/" + source.name
                receipt_path = destination.removesuffix(".md") + ".completion.json"
                arguments = dict(
                    run_id="portable-path-run", ticket_id="APM-02",
                    artifact_generation=0, configuration=projection_config("enabled"),
                    candidate_ref=candidate, source_relative_path=relative,
                    destination_relative_path=destination,
                    receipt_document=receipt, source_mode="tracked",
                )
                for field in ("source_relative_path", "destination_relative_path"):
                    for invalid in ("../outside.md", str(root / "outside.md")):
                        with self.assertRaises(ProjectionExcluded):
                            plan_tracked_completion(repo, **{**arguments, field: invalid})
                self.assertFalse((root / "outside.md").exists())
                if os.name == "nt":
                    # Native Windows Git control; this is not a simulated POSIX run.
                    env = dict(os.environ, GIT_INDEX_FILE=str(root / "native-index"))
                    subprocess.run(
                        ["git", "read-tree", tree], cwd=repo, env=env,
                        check=True, capture_output=True, timeout=30,
                    )
                    oid = git(repo, "hash-object", "--", relative).decode().strip()
                    native = receipt_path.replace("/", "\\")
                    rejected = subprocess.run(
                        ["git", "update-index", "--add", "--cacheinfo", f"100644,{oid},{native}"],
                        cwd=repo, env=env, capture_output=True, timeout=30,
                    )
                    self.assertEqual(128, rejected.returncode)
                # Exercise the actual Git mode, including hosts where chmod cannot
                # express an executable bit. No production mode guard is mocked.
                source.chmod(0o755)
                git(repo, "update-index", "--chmod=+x", "--", relative)
                mode_candidate = {
                    **candidate, "candidate_tree_oid": git(repo, "write-tree").decode().strip()
                }
                with self.assertRaisesRegex(ProjectionExcluded, "mode"):
                    plan_tracked_completion(repo, **{
                        **arguments, "candidate_ref": mode_candidate,
                        "receipt_document": {**receipt, "candidate_ref": mode_candidate},
                    })
                source.chmod(0o644)
                git(repo, "update-index", "--chmod=-x", "--", relative)
                planned = plan_tracked_completion(repo, **arguments)
                self.assertEqual(tree, git(repo, "write-tree").decode().strip())
                self.assertEqual(receipt_path, planned.manifest["completion_receipt"]["path"])
                self.assertEqual(
                    {relative, destination, receipt_path, "docs/specs/map.md"},
                    {row["path"] for row in planned.manifest["expected_diff"]},
                )
                self.assertFalse(any(planned.manifest["authority"].values()))
                malformed = copy.deepcopy(planned.manifest)
                malformed["completion_receipt"]["path"] = receipt_path.replace("/", "\\")
                malformed["manifest_digest"] = canonical_digest({
                    key: value for key, value in malformed.items() if key != "manifest_digest"
                })
                with self.assertRaisesRegex(FinalTreeProjectionError, "completion binding"):
                    validate_manifest(malformed)
                manifest_path = root / "manifest.json"
                manifest_path.write_bytes(planned.bytes)
                reference = projection_transaction_reference(
                    planned.manifest,
                    artifact=str(manifest_path),
                    sha256=hashlib.sha256(planned.bytes).hexdigest(),
                )
                state = root / "transaction.json"

                def save(value):
                    state.write_bytes(canonical_bytes(value))

                def load():
                    return json.loads(state.read_bytes())

                def started(key):
                    save(record_effect_started(load(), key)[0])

                def effect(key, readback):
                    save(record_effect_readback(load(), key, readback)[0])

                def checkpoint(actual_tree_oid, actual_diff_digest):
                    save(record_effects_checkpoint(
                        load(), actual_tree_oid=actual_tree_oid,
                        actual_diff_digest=actual_diff_digest,
                    )[0])

                def apply():
                    return apply_projection_transaction(
                        repo, planned.manifest, get_transaction=load,
                        persist_effect_started=started, persist_effect=effect,
                        persist_effects_readback=checkpoint,
                    )

                save(new_projection_transaction(reference, planned.manifest))
                result = apply()
                self.assertEqual("applied", result["result"])
                delivery = planned.manifest["planned_delivery_candidate_ref"]
                self.assertEqual(delivery, result["candidate_ref"])
                self.assertEqual(payload, (repo / destination).read_bytes())
                self.assertEqual(canonical_bytes(receipt), (repo / receipt_path).read_bytes())
                self.assertFalse(source.exists())
                self.assertEqual(
                    b"100644",
                    git(repo, "ls-tree", "-z", delivery["candidate_tree_oid"], "--", receipt_path).split(b" ", 1)[0],
                )
                self.assertEqual(
                    "parity",
                    compare_projection(repo, planned.manifest, delivery).document["status"],
                )
                save(record_final_tree_checkpoint(load(), delivery)[0])
                self.assertEqual("projected-not-integrated", load()["status"])
                prior_state = state.read_bytes()
                self.assertEqual("already-applied", apply()["result"])
                self.assertEqual(prior_state, state.read_bytes())
                self.assertEqual(
                    delivery["candidate_tree_oid"], git(repo, "write-tree").decode().strip()
                )
                self.assertEqual(b"", git(repo, "diff", "--name-only"))


if __name__ == "__main__":
    unittest.main()
