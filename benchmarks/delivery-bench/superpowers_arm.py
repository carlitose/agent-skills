"""Own the explicit Superpowers snapshot, skill isolation and content binding for one Pi arm."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import judge

ARM = "pi-superpowers"
BOOTSTRAP = ".pi/extensions/superpowers.ts"


class PackageError(ValueError):
    pass


def _digest(root: Path) -> str:
    # Git bookkeeping is not package content; ordinary status/fetch must not change the binding.
    entries = {}
    for path in sorted(root.iterdir()):
        if path.name == ".git":
            continue
        entries[path.name] = (judge.tree_digest(path)["sha256"] if path.is_dir()
                              else hashlib.sha256(path.read_bytes()).hexdigest())
    return hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()


def bind(arms: list[str], root: Path | None) -> dict | None:
    if ARM not in arms:
        if root is not None:
            raise PackageError("--superpowers-root requires the pi-superpowers arm")
        return None
    if root is None:
        raise PackageError("pi-superpowers requires --superpowers-root: a reviewed local snapshot")
    root = Path(root).resolve()
    try:
        package = json.loads((root / "package.json").read_text(encoding="utf-8"))
        if (not isinstance(package, dict) or package.get("name") != "superpowers"
                or not isinstance(package.get("version"), str) or not package["version"]
                or package.get("pi") != {"extensions": ["./" + BOOTSTRAP], "skills": ["./skills"]}):
            raise PackageError("Superpowers needs its supported native Pi manifest and version")
        if not (root / BOOTSTRAP).is_file():
            raise PackageError("Superpowers bootstrap is missing")
        skills = sorted(path.parent.name for path in (root / "skills").rglob("SKILL.md"))
        if "using-superpowers" not in skills or len(skills) != len(set(skills)):
            raise PackageError("Superpowers needs using-superpowers and unique skill names")
        return {"path": str(root), "version": package["version"], "sha256": _digest(root), "skills": skills}
    except (OSError, ValueError) as error:
        raise PackageError(f"Superpowers snapshot {root}: {error}") from None


def check(lot: dict, arm: str) -> dict | None:
    if arm != ARM:
        return None
    binding = lot.get("superpowers")
    if not isinstance(binding, dict) or not binding.get("path"):
        raise PackageError("the lot binds no Superpowers snapshot")
    if bind([ARM], Path(binding["path"])) != binding:
        raise PackageError("Superpowers changed after the lot was bound")
    return binding


def argv(lot: dict, arm: str) -> list[str]:
    binding = check(lot, arm)
    if binding is None:
        return []
    root = Path(binding["path"])
    # --no-skills suppresses discovery; explicit --skill paths still load (Pi resource loader).
    return ["-e", str(root / BOOTSTRAP), "--skill", str(root / "skills")]
