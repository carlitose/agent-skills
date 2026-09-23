"""Read the verify handoff the delivery renders from, and say what is wrong with it.

The delivery reads the verification bundle from two evidence entries of the verify
leaf result, `verification-checkpoint:bundle-validated` and `handoff-ready`, and
refuses any artifact outside the run directory. Until now that refusal came at the
delivery gate, after `stage verify pass`, from where no path leads back to verify
(q3, turns 169-199: the model built a junction into the run directory, approved its
own gate and merged by hand). The same reading now runs at `stage verify pass`, where
the ticket is still at verify and the remedy, the `verification-checkpoint` event,
is executable.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .leaf_protocol import rejection_detail
from .verification_checkpoint import checkpoint_remedy

BUNDLE_ID = "verification-checkpoint:bundle-validated"
HANDOFF_ID = "verification-checkpoint:handoff-ready"


class VerifyHandoffError(Exception):
    """The verify handoff cannot be read; ``detail`` names what to change."""

    def __init__(self, message: str, detail: Mapping[str, Any]):
        super().__init__(message)
        self.detail = dict(detail)


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def pending_verify_handoff(ticket: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """The recorded verify leaf result a `stage verify pass` would accept, if any.

    A recorded leaf result waits in ``leaf_handoff`` until its stage passes, which
    moves it to ``leaf_results[stage]``.
    """
    handoff = ticket.get("leaf_handoff")
    if isinstance(handoff, Mapping) and handoff.get("stage") == "verify":
        return handoff
    return None


def read_verify_handoff(
    ticket_id: str,
    ticket: Mapping[str, Any],
    *,
    ledger_path: Path,
    run_id: Any,
    handoff: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    """The validated bundle value and the artifact references the delivery records.

    ``handoff`` defaults to the passed verify result in ``leaf_results``; the stage
    event passes the pending one. Raises ``VerifyHandoffError`` naming the evidence
    field, the received artifact, the expected one and the step that produces it.
    """
    if handoff is None:
        handoff = ticket.get("leaf_results", {}).get("verify", {})
        field = f"tickets.{ticket_id}.leaf_results.verify.quality.evidence"
    else:
        field = f"tickets.{ticket_id}.leaf_handoff.quality.evidence"
    evidence = handoff.get("quality", {}).get("evidence", [])
    by_id = {item.get("id"): item for item in evidence if isinstance(item, Mapping)}
    run_dir = ledger_path.parent.resolve()
    remedy = checkpoint_remedy(run_id, ticket_id, ledger_path)
    bundle_reference = by_id.get(BUNDLE_ID)
    handoff_reference = by_id.get(HANDOFF_ID)
    if bundle_reference is None or handoff_reference is None:
        raise VerifyHandoffError(
            "verify handoff requires bundle-validated and handoff-ready artifacts",
            rejection_detail(
                field=field,
                received=sorted(str(key) for key in by_id),
                expected=(
                    f"entries with ids {BUNDLE_ID} and {HANDOFF_ID}, as the "
                    "verification-checkpoint event records them"
                ),
                next_step=remedy,
            ),
        )

    def load(reference: Mapping[str, Any], phase: str) -> tuple[Path, dict[str, Any], str]:
        entry = f"{field}[verification-checkpoint:{phase}].artifact"
        received = reference.get("artifact")
        try:
            path = Path(str(received)).resolve()
            path.relative_to(run_dir)
        except ValueError as error:
            raise VerifyHandoffError(
                f"verification handoff bundle is unreadable: {error}",
                rejection_detail(
                    field=entry,
                    received=received,
                    expected=f"a file under the run directory {run_dir}",
                    next_step=remedy,
                ),
            ) from error
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            recorded_hash = document["artifact_hash"]
        except (KeyError, OSError, UnicodeError, ValueError, TypeError) as error:
            raise VerifyHandoffError(
                f"verification handoff bundle is unreadable: {error}",
                rejection_detail(
                    field=entry,
                    received=received,
                    expected=(
                        "a readable JSON artifact with artifact_hash, as the "
                        "verification-checkpoint event writes it"
                    ),
                    next_step=remedy,
                ),
            ) from error
        payload = {key: value for key, value in document.items() if key != "artifact_hash"}
        if (
            recorded_hash != reference.get("sha256")
            or canonical_digest(payload) != recorded_hash
            or document.get("phase") != phase
            or document.get("candidate_ref") != ticket["candidate_ref"]
            or not isinstance(document.get("value"), dict)
        ):
            raise VerifyHandoffError(
                f"verification {phase} artifact is invalid",
                rejection_detail(
                    field=entry,
                    received=received,
                    expected=(
                        f"the {phase} artifact the verification-checkpoint wrote for "
                        "this candidate: its sha256 in the evidence, its phase, its "
                        "candidate_ref and a JSON object value"
                    ),
                    next_step=remedy,
                ),
            )
        return path, document, recorded_hash

    bundle_path, bundle_document, bundle_hash = load(bundle_reference, "bundle-validated")
    _path, _document, handoff_hash = load(handoff_reference, "handoff-ready")
    return bundle_document["value"], {
        "artifact": str(bundle_path),
        "sha256": bundle_hash,
        "handoff_sha256": handoff_hash,
    }
