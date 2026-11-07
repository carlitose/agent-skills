"""Same-content physical addresses for frozen profile entries; never edits lot.json."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

FILE = "extension-relocations.json"


class RelocationError(ValueError):
    """An address override does not preserve the original frozen binding."""


def _bindings(lot: dict) -> dict:
    bindings = {}
    for entries in lot.get("arm_extensions", {}).values():
        for entry in entries:
            path = Path(entry["path"])
            if path in bindings and bindings[path] != entry["sha256"]:
                raise RelocationError("conflicting original extension digests")
            bindings[path] = entry["sha256"]
    return bindings


def _empty(directory: Path, lot: dict) -> dict:
    return {"schema": 1, "lot_sha256": hashlib.sha256((directory / "lot.json").read_bytes()).hexdigest(),
            "authority_sha256": lot["authority"]["sha256"], "entries": []}


def _validate(document: dict, directory: Path, lot: dict) -> dict:
    expected = _empty(directory, lot)
    if (not isinstance(document, dict) or set(document) != set(expected)
            or type(document["schema"]) is not int or document["schema"] != 1
            or not isinstance(document["entries"], list)):
        raise RelocationError("invalid extension relocation metadata")
    if document["lot_sha256"] != expected["lot_sha256"]:
        raise RelocationError("relocation metadata is bound to another manifest")
    if document["authority_sha256"] != expected["authority_sha256"]:
        raise RelocationError("relocation metadata is bound to another authority")
    bindings = _bindings(lot)
    latest = {}
    for entry in document["entries"]:
        if (not isinstance(entry, dict) or set(entry) != {"source", "snapshot", "sha256", "reason", "at"}
                or not all(isinstance(v, str) and v.strip() for v in entry.values())):
            raise RelocationError("invalid extension relocation entry")
        source, snapshot = Path(entry["source"]), Path(entry["snapshot"])
        if not source.is_absolute() or source not in bindings:
            raise RelocationError("relocation source is not an original bound entrypoint")
        if not snapshot.is_absolute() or source == snapshot or source.name != snapshot.name:
            raise RelocationError("relocation must preserve the entrypoint name at a different absolute path")
        if entry["sha256"] != bindings[source]:
            raise RelocationError("relocation cannot replace the frozen extension digest")
        latest[source] = entry
    return latest


def _read(directory: Path, lot: dict) -> dict:
    path = directory / FILE
    if not path.exists():
        return _empty(directory, lot)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as error:
        raise RelocationError(f"invalid extension relocation metadata: {error}") from None
    return document


def apply(directory: Path, lot: dict, document: dict | None = None) -> None:
    """Overlay only addresses. The runner then performs its unchanged full content checks."""
    document = _read(directory, lot) if document is None else document
    latest = _validate(document, directory, lot)
    for entries in lot.get("arm_extensions", {}).values():
        for entry in entries:
            relocation = latest.get(Path(entry["path"]))
            if relocation:
                entry["path"] = relocation["snapshot"]


def propose(directory: Path, lot: dict, source: Path, snapshot: Path, reason: str, at: str) -> tuple:
    """Plan one update, retaining previous entries; no filesystem mutation or content waiver."""
    if not reason.strip():
        raise RelocationError("an extension relocation needs a reason")
    bindings = _bindings(lot)
    source, snapshot = Path(source).resolve(), Path(snapshot).resolve()
    if source not in bindings:
        raise RelocationError("relocation source is not an original bound entrypoint")
    document = _read(directory, lot)
    latest = _validate(document, directory, lot).get(source)
    if latest and Path(latest["snapshot"]) == snapshot:
        return document, False
    entry = {"source": str(source), "snapshot": str(snapshot), "sha256": bindings[source],
             "reason": reason.strip(), "at": at}
    document["entries"].append(entry)
    _validate(document, directory, lot)
    return document, True
