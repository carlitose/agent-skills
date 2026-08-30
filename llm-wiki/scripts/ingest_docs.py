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
    python3 ingest_docs.py <wiki-root> [--autopilot-root <path>] [--dry-run] [--json]
"""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from date_provenance import disposition_of, resolve_artefact_dates  # noqa: E402
from project_binding import discover_artefacts, resolve_project_root  # noqa: E402
from session_catalog import render_session_catalog, session_entries  # noqa: E402

SOURCES_DIRECTORY = ("wiki", "sources")
INDEX_PATH = ("wiki", "index.md")
TIMELINE_INDEX = ("wiki", "timeline", "index.md")
ARTIFACT_ID = re.compile(r"(?m)^- Artifact ID:\s*`([^`]+)`")
PARENT_LINK = re.compile(r"(?m)^- Parent:\s*\[[^\]]*\]\(([^)]+)\)")
#: The repository's Artifact Graph puts downward edges under one of three headings and
#: requires them to be reciprocal. Compiling only the upward half left every decision
#: spec with no inbound link, so every one of them read as an orphan.
DOWNWARD_HEADINGS = ("### Children", "### Produces", "### Related")
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
#: ``[ \t]*`` rather than ``\s*``: ``\s`` matches a newline, so an empty value such as
#: ``disposition_changed:`` swallowed the following line and its key vanished from the parse.
#: An empty value is exactly what an unknown date produces, so the bug hid the provenance of
#: every date the ladder could not resolve.
FRONT_MATTER = re.compile(r"(?m)^(?P<key>[a-z_]+):[ \t]*(?P<value>.*)$")
TRANSITIONS = ("unchanged", "new", "changed", "moved", "missing")


class TicketParserError(RuntimeError):
    """The canonical ticket parser is absent or could not parse a ticket."""


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
    children: tuple[str, ...] = ()
    blocked_by: tuple[str, ...] = ()
    run_id: str | None = None
    dates: dict[str, object] = field(default_factory=dict)

    @property
    def weak_identity(self) -> bool:
        return self.identity_key.startswith("path:")


def downward_links(text: str) -> tuple[str, ...]:
    """The link targets under an Artifact Graph's downward headings, in order.

    Reads only until the next heading of the same or higher level, so a `Children` list
    does not swallow the section after it.
    """

    found: list[str] = []
    collecting = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped in DOWNWARD_HEADINGS:
            collecting = True
            continue
        if stripped.startswith("#"):
            collecting = False
            continue
        if collecting and stripped.startswith("- "):
            found += MARKDOWN_LINK.findall(stripped)
    return tuple(dict.fromkeys(found))


def source_digest(path: Path) -> str:
    """``sha256`` over universal-newline text, so a CRLF checkout is not all-changed.

    Reuses the repository's own idiom: ``ticket_contract.read_ticket_text`` opens with
    ``newline=None`` before hashing, and ``WT-06`` recorded what goes wrong otherwise.
    """

    with path.open("r", encoding="utf-8", newline=None, errors="replace") as handle:
        text = handle.read()
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def default_autopilot_root() -> Path:
    """Resolve ticket-autopilot as a sibling of this installed skill.

    The same layout holds in this source repository and under ``.agents/skills``. The
    project bound to the wiki is unrelated to either skill's installation directory.
    """

    return Path(__file__).resolve().parents[2] / "ticket-autopilot"


def _ticket_envelope(autopilot_root: Path, path: Path) -> dict:
    """Parse a ticket through the canonical CLI, never by reading YAML here.

    A file under ``docs/tickets/`` may never fall through to Artifact ID classification.
    Doing so changes both its kind and its stable identity, which can mint duplicate pages.
    """

    script = autopilot_root / "scripts" / "ticket-autopilot.py"
    if not script.is_file():
        raise TicketParserError(
            f"ticket parser is unavailable: expected {script}; install ticket-autopilot "
            "beside llm-wiki or pass --autopilot-root <path>"
        )
    result = subprocess.run(
        [sys.executable, "-B", str(script), "ticket-parse", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        suffix = f": {detail}" if detail else ""
        raise TicketParserError(
            f"canonical ticket parser failed for {path} (exit {result.returncode}){suffix}"
        )
    try:
        envelope = json.loads(result.stdout)["data"]["envelope"]
    except (json.JSONDecodeError, KeyError, TypeError):
        raise TicketParserError(
            f"canonical ticket parser returned an invalid envelope for {path}"
        ) from None
    if not isinstance(envelope, dict) or not envelope.get("ticket_id"):
        raise TicketParserError(
            f"canonical ticket parser returned an invalid envelope for {path}"
        )
    return envelope


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
    is_ticket_path = relative_path.startswith("docs/tickets/")
    envelope = _ticket_envelope(autopilot_root, path) if is_ticket_path else None
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
        children=downward_links(text),
        blocked_by=blocked,
        run_id=run_id,
        dates=resolve_artefact_dates(project_root, relative_path),
    )


def page_name(artefact: Artefact) -> str:
    """A filename derived from identity, so a move never mints a second page."""

    stem = re.sub(r"[^a-z0-9]+", "-", artefact.identity_key.casefold()).strip("-")
    return f"{stem}.md"


DISPOSITION_DIRECTORIES = ("done", "canceled", "hold")


class LinkIndex:
    """Identity and repository path to page stem, so a graph edge links a page.

    Without this, ``blocked_by`` renders the identity key as the wikilink target and the link
    is dead: the page is named from the identity's *slug*. The parent edge needs the path form
    because an ``## Artifact Graph`` names its parent by relative path, not by identity.
    """

    def __init__(self, corpus: dict) -> None:
        stems = {key: page_name(artefact)[:-3] for key, artefact in corpus.items()}
        self.by_identity = stems
        self.by_path = {
            artefact.relative_path: stems[key] for key, artefact in corpus.items()
        }

    def identity(self, key: str) -> str | None:
        return self.by_identity.get(key)

    def relative_link(self, source_relative_path: str, link: str) -> str | None:
        """Resolve a relative link from an artefact, tolerating a disposition move.

        A ticket's ``Parent: ../../specs/foo.md`` was written for its open location. Once the
        ticket moves into ``done/`` the literal resolution is one level short, so the
        disposition directory is stripped and the resolution retried. The same drift that
        `artifact-audit` learned to tolerate.
        """

        base = posixpath.dirname(source_relative_path)
        candidates = [base]
        if posixpath.basename(base) in DISPOSITION_DIRECTORIES:
            candidates.append(posixpath.dirname(base))
        for candidate in candidates:
            resolved = posixpath.normpath(posixpath.join(candidate, link))
            stem = self.by_path.get(resolved)
            if stem is not None:
                return stem
        return None


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


def render_page(
    artefact: Artefact, *, source_status: str = "present", links: "LinkIndex | None" = None
) -> str:
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
        "disposition_changed:"
        + (f" {dates['disposition_changed']}" if dates.get("disposition_changed") else ""),
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
    if artefact.parent or artefact.children or artefact.blocked_by:
        lines += ["", "## Graph", ""]
        if artefact.parent:
            stem = (
                links.relative_link(artefact.relative_path, artefact.parent)
                if links
                else None
            )
            if stem:
                lines.append(f"- Parent source: [[sources/{stem}]]")
            else:
                lines.append(
                    f"- Parent source: `{artefact.parent}` — not in this wiki, so there is "
                    "nothing to link to"
                )
        for child in artefact.children:
            stem = (
                links.relative_link(artefact.relative_path, child) if links else None
            )
            if stem:
                lines.append(f"- Child source: [[sources/{stem}]]")
            else:
                lines.append(
                    f"- Child source: `{child}` — not in this wiki, so there is nothing "
                    "to link to"
                )
        for blocker in artefact.blocked_by:
            folder = Path(artefact.relative_path).parent
            if folder.name in DISPOSITION_DIRECTORIES:
                folder = folder.parent
            identity = f"ticket:{folder.name}/{blocker}"
            stem = links.identity(identity) if links else None
            if stem:
                lines.append(f"- Blocked by: [[sources/{stem}]] — `{identity}`")
            else:
                lines.append(
                    f"- Blocked by: `{identity}` — not in this wiki, so there is nothing "
                    "to link to"
                )
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

    links = LinkIndex(corpus)
    for name in ("new", "changed", "moved"):
        for identity in transitions[name]:
            artefact = corpus[identity]
            page = sources / page_name(artefact)
            if not dry_run:
                sources.mkdir(parents=True, exist_ok=True)
                page.write_text(render_page(artefact, links=links), encoding="utf-8")
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
    if wiki_root.joinpath(*TIMELINE_INDEX).is_file():
        # Only once it exists. Listing it earlier would put a dead link in the catalog and
        # make the lint's own index the first thing that fails.
        lines += [
            "## Timeline",
            "",
            "- [[timeline/index]] — when each artefact happened, and how each date is known",
            "",
        ]
    text = render_session_catalog("\n".join(lines), session_entries(wiki_root))
    index.write_text(text, encoding="utf-8")


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__)
        return 0
    wiki_root = Path(argv[0])
    autopilot_root = default_autopilot_root()
    if "--autopilot-root" in argv[1:]:
        option = argv.index("--autopilot-root")
        if option + 1 >= len(argv):
            print("error: --autopilot-root requires a path", file=sys.stderr)
            return 2
        autopilot_root = Path(argv[option + 1])
    try:
        report = ingest(
            wiki_root, autopilot_root, dry_run="--dry-run" in argv[1:]
        )
    except TicketParserError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
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
