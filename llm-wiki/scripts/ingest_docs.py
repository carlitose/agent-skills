#!/usr/bin/env python3
"""Compile a project's own ``docs/`` tree into wiki source pages, idempotently.

The first ingest of a clean tree cannot fail. Every ingest after it can, and silently, which is
why this module keys pages on identity rather than on path:

* a **ticket** is ``ticket:<spec-slug>/<ticket_id>``, read through the canonical
  ``ticket-parse`` CLI so ``blocked_by`` is never inferred from a heading;
* a **spec** with an ``## Artifact Graph`` is its ``Artifact ID``;
* anything else falls back to ``path:<repo-relative-path>``, a **weak** key that cannot
  survive a move and is labelled as such on the page.

Classification is set-based. The whole corpus is resolved before anything is decided, because a
per-file pass sees a delete before its matching add and reports one moved artefact as a deletion
plus a creation.

Five transitions, each with one page action:

===========  ==================================================  ================
transition   page action                                         timeline event
===========  ==================================================  ================
unchanged    nothing is written and ``updated`` is untouched      none
new          create the page and index it                         created
changed      rewrite the body, bump ``updated``                   amended
moved        keep the page and its identity, rewrite the source   disposition-changed / moved
missing      tombstone: keep the page, mark ``source_status``      source-removed
===========  ==================================================  ================

The graph already exists in the artefacts — ``Artifact ID``, ``Parent``, ``blocked_by`` — so it
is materialised as wikilinks rather than guessed into a parallel ``related:`` list that would
drift immediately.

Usage:
    python3 ingest_docs.py <wiki-root> [--dry-run] [--json]
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from date_provenance import disposition_of, resolve_artefact_dates  # noqa: E402
from project_binding import discover_artefacts, read_binding, resolve_project_root  # noqa: E402

SOURCES_DIRECTORY = ("wiki", "sources")
INDEX_PATH = ("wiki", "index.md")
ARTIFACT_ID = re.compile(r"(?m)^- Artifact ID:\s*`([^`]+)`")
PARENT_LINK = re.compile(r"(?m)^- Parent:\s*\[[^\]]*\]\(([^)]+)\)")
#: ``[ \t]*`` rather than ``\s*``: ``\s`` matches a newline, so an empty value such as
#: ``disposition_changed:`` swallowed the following line and its key vanished from the parse.
#: An empty value is exactly what an unknown date produces, so the bug hid the provenance of
#: every date the ladder could not resolve.
FRONT_MATTER = re.compile(r"(?m)^(?P<key>[a-z_]+):[ \t]*(?P<value>.*)$")
TRANSITIONS = ("unchanged", "new", "changed", "moved", "missing")


@dataclass
class Artefact:
    """One source artefact, with the identity that survives its moves."""

    relative_path: str
    identity_key: str
    kind: str
    digest: str
    disposition: str
    title: str
    artifact_id: str | None = None
    parent: str | None = None
    blocked_by: tuple[str, ...] = ()
    run_id: str | None = None
    dates: dict[str, object] = field(default_factory=dict)

    @property
    def weak_identity(self) -> bool:
        return self.identity_key.startswith("path:")


def source_digest(path: Path) -> str:
    """``sha256`` over universal-newline text, so a CRLF checkout is not all-changed.

    Reuses the repository's own idiom: ``ticket_contract.read_ticket_text`` opens with
    ``newline=None`` before hashing, and ``WT-06`` recorded what goes wrong otherwise.
    """

    with path.open("r", encoding="utf-8", newline=None, errors="replace") as handle:
        text = handle.read()
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _ticket_envelope(autopilot_root: Path, path: Path) -> dict | None:
    """Parse a ticket through the canonical CLI, never by reading YAML here."""

    script = autopilot_root / "scripts" / "ticket-autopilot.py"
    if not script.is_file():
        return None
    result = subprocess.run(
        [sys.executable, "-B", str(script), "ticket-parse", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)["data"]["envelope"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def _title_of(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    except OSError:
        pass
    return path.stem


def classify(
    project_root: Path, relative_path: str, autopilot_root: Path
) -> Artefact:
    """Resolve one artefact's identity, kind and metadata."""

    path = project_root / relative_path
    text = path.read_text(encoding="utf-8", errors="replace")
    digest = source_digest(path)
    disposition = disposition_of(relative_path)
    title = _title_of(path)
    artifact_match = ARTIFACT_ID.search(text)
    parent_match = PARENT_LINK.search(text)
    envelope = (
        _ticket_envelope(autopilot_root, path)
        if relative_path.startswith("docs/tickets/")
        else None
    )
    if envelope is not None:
        folder = Path(relative_path).parent
        if folder.name in {"done", "canceled", "hold"}:
            folder = folder.parent
        identity = f"ticket:{folder.name}/{envelope['ticket_id']}"
        kind = "ticket"
        blocked = tuple(envelope.get("blocked_by") or ())
    elif artifact_match is not None:
        identity = artifact_match.group(1)
        kind = "spec"
        blocked = ()
    else:
        identity = f"path:{relative_path}"
        kind = "other"
        blocked = ()
    completion = path.with_suffix(".completion.json")
    run_id = None
    if completion.is_file():
        try:
            run_id = json.loads(completion.read_text(encoding="utf-8")).get("run_id")
        except (OSError, json.JSONDecodeError):
            run_id = None
    return Artefact(
        relative_path=relative_path,
        identity_key=identity,
        kind=kind,
        digest=digest,
        disposition=disposition if kind == "ticket" else "not-applicable",
        title=title,
        artifact_id=artifact_match.group(1) if artifact_match else None,
        parent=parent_match.group(1) if parent_match else None,
        blocked_by=blocked,
        run_id=run_id,
        dates=resolve_artefact_dates(project_root, relative_path),
    )


def page_name(artefact: Artefact) -> str:
    """A filename derived from identity, so a move never mints a second page."""

    stem = re.sub(r"[^a-z0-9]+", "-", artefact.identity_key.casefold()).strip("-")
    return f"{stem}.md"


def read_page_front_matter(path: Path) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    block = text[3:end] if end != -1 else text
    return {
        match.group("key"): match.group("value").strip()
        for match in FRONT_MATTER.finditer(block)
    }


def render_page(artefact: Artefact, *, source_status: str = "present") -> str:
    """Render one source page. Fields are flat scalars, per the identity contract."""

    dates = artefact.dates
    lines = [
        "---",
        "type: source",
        f'title: "{artefact.title}"',
        f"identity_key: {artefact.identity_key}",
        f"identity_strength: {'weak' if artefact.weak_identity else 'stable'}",
        f"source_path: {artefact.relative_path}",
        f"source_digest: {artefact.digest}",
        f"source_status: {source_status}",
        f"artefact_kind: {artefact.kind}",
        f"disposition: {artefact.disposition}",
        f"created: {dates.get('created') or ''}",
        f"created_provenance: {dates.get('created_provenance')}",
        f"disposition_changed: {dates.get('disposition_changed') or ''}",
        f"disposition_changed_provenance: {dates.get('disposition_changed_provenance')}",
    ]
    if artefact.run_id:
        lines.append(f"run_id: {artefact.run_id}")
    lines += ["---", "", f"# {artefact.title}", ""]
    lines.append(
        f"Compiled from `{artefact.relative_path}`. Identity is "
        f"`{artefact.identity_key}`, which is why moving the artefact between dispositions "
        "updates this page instead of creating a second one."
    )
    if artefact.weak_identity:
        lines += [
            "",
            "**This artefact has no stable identifier.** It carries neither a ticket envelope "
            "nor an `## Artifact Graph`, so its identity is its path at first ingest. Moving "
            "it will read as a deletion plus a creation, and the repair is to give the source "
            "an `## Artifact Graph`.",
        ]
    lines += ["", "## Dates", ""]
    for label, value_key, provenance_key in (
        ("Created", "created", "created_provenance"),
        ("Disposition changed", "disposition_changed", "disposition_changed_provenance"),
    ):
        value = dates.get(value_key)
        provenance = dates.get(provenance_key)
        if value:
            marker = " (low confidence)" if dates.get(f"{value_key}_low_confidence") else ""
            lines.append(f"- {label}: **{value}** via `{provenance}`{marker}")
        else:
            lines.append(f"- {label}: **unknown** — no rung produced a date")
    if artefact.parent or artefact.blocked_by:
        lines += ["", "## Graph", ""]
        if artefact.parent:
            lines.append(f"- Parent source: `{artefact.parent}`")
        for blocker in artefact.blocked_by:
            folder = Path(artefact.relative_path).parent
            if folder.name in {"done", "canceled", "hold"}:
                folder = folder.parent
            lines.append(f"- Blocked by: [[ticket:{folder.name}/{blocker}]]")
    if artefact.run_id:
        lines += [
            "",
            "## Run",
            "",
            f"Completed under autopilot run `{artefact.run_id}`, taken from the "
            "`completion.json` beside the source. That sidecar carries no date, so nothing "
            "here is dated from it.",
        ]
    lines.append("")
    return "\n".join(lines)


def plan(wiki_root: Path, autopilot_root: Path) -> dict[str, object]:
    """Resolve the whole corpus and the whole wiki, then classify every transition."""

    project_root = resolve_project_root(wiki_root)
    sources = wiki_root.joinpath(*SOURCES_DIRECTORY)
    corpus: dict[str, Artefact] = {}
    for relative in discover_artefacts(wiki_root):
        artefact = classify(project_root, relative, autopilot_root)
        corpus[artefact.identity_key] = artefact

    existing: dict[str, tuple[Path, dict[str, str]]] = {}
    if sources.is_dir():
        for page in sorted(sources.glob("*.md")):
            matter = read_page_front_matter(page)
            identity = matter.get("identity_key")
            if identity:
                existing[identity] = (page, matter)

    transitions: dict[str, list[str]] = {name: [] for name in TRANSITIONS}
    events: list[dict[str, str]] = []
    for identity, artefact in corpus.items():
        if identity not in existing:
            transitions["new"].append(identity)
            events.append({"identity": identity, "event": "created"})
            continue
        _page, matter = existing[identity]
        moved = matter.get("source_path") != artefact.relative_path
        changed = matter.get("source_digest") != artefact.digest
        if moved:
            transitions["moved"].append(identity)
            events.append(
                {
                    "identity": identity,
                    "event": (
                        "disposition-changed"
                        if matter.get("disposition") != artefact.disposition
                        else "moved"
                    ),
                }
            )
        elif changed:
            transitions["changed"].append(identity)
            events.append({"identity": identity, "event": "amended"})
        else:
            transitions["unchanged"].append(identity)
    for identity in existing:
        if identity not in corpus and existing[identity][1].get("source_status") != "missing":
            transitions["missing"].append(identity)
            events.append({"identity": identity, "event": "source-removed"})
    return {
        "project_root": str(project_root),
        "corpus": corpus,
        "existing": existing,
        "transitions": transitions,
        "events": events,
    }


def ingest(
    wiki_root: Path, autopilot_root: Path, *, dry_run: bool = False
) -> dict[str, object]:
    """Apply the plan. ``unchanged`` writes nothing at all, which is the idempotence bar."""

    resolved = plan(wiki_root, autopilot_root)
    corpus: dict[str, Artefact] = resolved["corpus"]  # type: ignore[assignment]
    existing = resolved["existing"]
    transitions = resolved["transitions"]
    sources = wiki_root.joinpath(*SOURCES_DIRECTORY)
    written: list[str] = []

    for name in ("new", "changed", "moved"):
        for identity in transitions[name]:
            artefact = corpus[identity]
            page = sources / page_name(artefact)
            if not dry_run:
                sources.mkdir(parents=True, exist_ok=True)
                page.write_text(render_page(artefact), encoding="utf-8")
            written.append(page.name)
    for identity in transitions["missing"]:
        page, matter = existing[identity]  # type: ignore[index]
        if dry_run:
            written.append(page.name)
            continue
        text = page.read_text(encoding="utf-8", errors="replace")
        text = text.replace("source_status: present", "source_status: missing", 1)
        if "source_status: missing" not in text:
            text = text.replace("---\n", "---\nsource_status: missing\n", 1)
        page.write_text(text, encoding="utf-8")
        written.append(page.name)

    if not dry_run and written:
        _write_index(wiki_root, corpus, existing)
    return {
        "project_root": resolved["project_root"],
        "artefacts": len(corpus),
        "transitions": {name: len(items) for name, items in transitions.items()},
        "events": resolved["events"],
        "written": sorted(written),
        "weak_identities": sorted(
            key for key, artefact in corpus.items() if artefact.weak_identity
        ),
    }


def _write_index(wiki_root: Path, corpus: dict[str, Artefact], existing) -> None:
    """Rebuild the index so every page appears exactly once."""

    index = wiki_root.joinpath(*INDEX_PATH)
    index.parent.mkdir(parents=True, exist_ok=True)
    by_kind: dict[str, list[Artefact]] = {}
    for artefact in corpus.values():
        by_kind.setdefault(artefact.kind, []).append(artefact)
    lines = ["# Index", "", "> Project history compiled from the repository's own `docs/`.", ""]
    for kind in sorted(by_kind):
        lines += [f"## {kind.title()} sources", ""]
        for artefact in sorted(by_kind[kind], key=lambda item: item.identity_key):
            stem = page_name(artefact)[:-3]
            lines.append(f"- [[sources/{stem}]] — {artefact.title}")
        lines.append("")
    tombstones = [
        identity
        for identity in existing
        if identity not in corpus
    ]
    if tombstones:
        lines += ["## Removed sources", ""]
        for identity in sorted(tombstones):
            lines.append(f"- `{identity}` — the source artefact no longer exists")
        lines.append("")
    index.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__)
        return 0
    wiki_root = Path(argv[0])
    autopilot = Path(read_binding(wiki_root).get("autopilot_root", "")) if False else None
    autopilot_root = resolve_project_root(wiki_root) / "ticket-autopilot"
    report = ingest(
        wiki_root, autopilot_root, dry_run="--dry-run" in argv[1:]
    )
    if "--json" in argv[1:]:
        printable = {key: value for key, value in report.items()}
        print(json.dumps(printable, indent=2, sort_keys=True, default=str))
        return 0
    print(f"project     {report['project_root']}")
    print(f"artefacts   {report['artefacts']}")
    for name, count in report["transitions"].items():
        print(f"  {name:10} {count}")
    print(f"written     {len(report['written'])}")
    print(f"weak keys   {len(report['weak_identities'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
