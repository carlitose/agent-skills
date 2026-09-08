#!/usr/bin/env python3
"""NON-PRODUCTION semantic projection experiment; writes only disposable fixtures.

Run without arguments for measurements, or --output results.json to retain all
compared pages. No real wiki, source, provider, ledger or installed skill is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "llm-wiki" / "scripts"))
import ingest_docs as production  # noqa: E402
from project_binding import DEFAULT_DOCS_GLOBS, write_binding  # noqa: E402
from root_catalog import initialize_catalog  # noqa: E402
from fixtures import AUTHORED, EDITED_FACT, FIXTURES, LATE_FACT, QUESTIONS  # noqa: E402

AUTOPILOT = ROOT / "ticket-autopilot"
VARIANTS = ("metadata-control", "preserve", "bounded", "layered")
SECTION_LIMIT = 220  # Unicode characters, deliberately not a token estimate.
FIXED_MTIME = 1700000000
START = "<!-- prototype-source:start -->"
END = "<!-- prototype-source:end -->"
ALIASES = {
    "intent": {"what to build", "destination", "purpose", "prototype frame"},
    "acceptance": {"acceptance criteria"},
    "testing": {"testing plan", "verification approach", "reproduce", "run"},
    "frontier": {"frontier", "frontier blocking edges", "keep discard decide"},
    "exclusions": {"out of scope", "limits", "limitations"},
    "decisions": {"decisions", "decisions so far", "result", "operator behavior"},
    "evidence": {"evidence", "result"},
}


def digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def sections(text: str) -> dict[str, list[str]]:
    """Tiny ATX-only prototype: retain duplicates; ignore fenced fake headings.

    Setext headings are intentionally unsupported and measured as a limitation.
    This does NOT parse Ticket Envelope metadata; production ticket-parse does.
    """
    found: dict[str, list[str]] = {}
    heading = None
    block: list[str] = []
    fence = None

    def flush() -> None:
        if heading is not None:
            found.setdefault(heading, []).append("\n".join(block).strip())

    for line in text.splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            block.append(line)
            continue
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line) if fence is None else None
        if match:
            flush()
            heading = " ".join(re.sub(r"[^\w\s]", " ", match[1].casefold()).split())
            block = []
        else:
            block.append(line)
    flush()
    return found


def bounded(text: str) -> str:
    parsed = sections(text)
    blocks = ["## Structured extract", "", "Deterministic excerpts; no authored synthesis."]
    for question in QUESTIONS:
        chunks = [body for heading, bodies in parsed.items()
                  if heading in ALIASES[question] for body in bodies if body]
        content = "\n\n".join(chunks)
        if not content:
            excerpt = "UNAVAILABLE: no recognized nonempty section."
        elif len(content) > SECTION_LIMIT:
            excerpt = content[:SECTION_LIMIT] + "\n[TRUNCATED: consult the source-preserving option.]"
        else:
            excerpt = content
        blocks += ["", f"### {question}", excerpt]
    return "\n".join(blocks) + "\n"


def preserve(text: str) -> str:
    # A literal block keeps source-relative links from becoming broken wiki links.
    # The fence is longer than any source backtick fence, including guide examples.
    lengths = [len(m[0]) for m in re.finditer(r"(?m)^`+", text)]
    fence = "`" * max(3, max(lengths, default=0) + 1)
    return ("## Preserved source (literal Markdown)\n\n" + START + "\n"
            + fence + "markdown\n" + text + "\n" + fence + "\n" + END + "\n")


def recover_preserved(page: str) -> str:
    block = page.split(START + "\n", 1)[1].split("\n" + END, 1)[0]
    return block.split("\n", 1)[1].rsplit("\n", 1)[0]


def body(page: str) -> str:
    return page.split("\n---\n", 1)[1] if page.startswith("---\n") else page


def size(text: str) -> dict[str, int]:
    return {"bytes": len(text.encode("utf-8")), "words": len(text.split())}


def utility(page: str, answers: dict) -> dict[str, str]:
    # Independent explicit answer witnesses; never extracted from the option's
    # own heading map. This is lexical recoverability, NOT a live reader study.
    visible = " ".join(body(page).split())
    return {q: "absent-in-source" if answers.get(q) is None else
            "answerable" if " ".join(answers[q].split()) in visible else
            "missing-from-page" for q in QUESTIONS}


class Experiment:
    def __init__(self, root: Path, variant: str):
        if variant not in VARIANTS:
            raise ValueError(variant)
        self.variant = variant
        self.project = root / "project"
        self.wiki = root / "PROTOTYPE-wipe-me"
        self.wiki.mkdir()
        for fixture in FIXTURES:
            self.put(fixture["path"], fixture["text"])
        # Guides are required by SW-01 but absent from the real/default binding.
        write_binding(self.wiki, self.project, docs_globs=DEFAULT_DOCS_GLOBS +
                      ("docs/guides/*.md",), git_mode="off", session_providers=())
        (self.wiki / "purpose.md").write_text("# Disposable fixture comparison\n", encoding="utf-8")
        (self.wiki / "schema.md").write_text("# Prototype-only source and summary pages\n", encoding="utf-8")
        index = self.wiki / "wiki" / "index.md"
        index.parent.mkdir()
        text = initialize_catalog()
        if variant == "layered":
            text += "\n## Experimental summaries\n- [[synthesis/index]]\n"
        index.write_text(text, encoding="utf-8")
        self.authored = {}
        for fixture in FIXTURES:
            artefact = self.classify(fixture["path"])
            self.authored[artefact.identity_key] = {
                "digest": artefact.digest, "text": AUTHORED[fixture["path"]],
            }

    def put(self, relative: str, text: str) -> None:
        path = self.project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        os.utime(path, (FIXED_MTIME, FIXED_MTIME))

    def classify(self, relative: str):
        return production.classify(self.project, relative, AUTOPILOT)

    def pages(self) -> dict[str, str]:
        return {p.relative_to(self.wiki).as_posix(): p.read_text(encoding="utf-8")
                for p in sorted((self.wiki / "wiki").rglob("*.md"))}

    def page_path(self, identity: str) -> Path:
        return next(p for p in (self.wiki / "wiki" / "sources").glob("*.md")
                    if production.read_page_front_matter(p)["identity_key"] == identity)

    def summaries(self) -> int:
        directory = self.wiki / "wiki" / "synthesis"
        directory.mkdir(exist_ok=True)
        writes = 0
        links = []
        for source in sorted((self.wiki / "wiki" / "sources").glob("*.md")):
            matter = production.read_page_front_matter(source)
            authored = self.authored.get(matter["identity_key"])
            freshness = ("source-missing" if matter["source_status"] == "missing" else
                         "unavailable" if authored is None else
                         "digest-match" if authored["digest"] == matter["source_digest"] else "stale")
            name = source.stem + "-summary"
            text = (f"# Agent-authored fixture summary\n\n"
                    f"Source: [[sources/{source.stem}]]\n\n"
                    f"Freshness: {freshness}; audit: unreviewed.\n"
                    f"Authored against: {authored['digest'] if authored else 'unavailable'}\n\n"
                    "Handwritten for this experiment; no LLM call or approval is implied.\n"
                    "A matching digest does not prove semantic correctness.\n\n"
                    + (authored["text"] if authored else "No authored summary available.") + "\n")
            if freshness != "digest-match":
                text += "\nDo not treat this summary as current; authoring/review is required.\n"
            writes += self.write_changed(directory / (name + ".md"), text)
            links.append(f"- [[synthesis/{name}]]")
        writes += self.write_changed(directory / "index.md", "# Experimental summaries\n\n" + "\n".join(links) + "\n")
        return writes

    @staticmethod
    def write_changed(path: Path, text: str) -> int:
        encoded = text.encode("utf-8")
        if path.exists() and path.read_bytes() == encoded:
            return 0
        path.write_bytes(encoded)
        return len(encoded)

    def run(self) -> dict:
        original = production.render_page
        before = self.pages()

        def render(artefact, **kwargs):
            metadata = original(artefact, **kwargs)
            if self.variant == "metadata-control":
                return metadata
            text = (self.project / artefact.relative_path).read_text(encoding="utf-8")
            projection = bounded(text) if self.variant == "bounded" else preserve(text)
            if self.variant == "layered":
                projection += "\n## Derived summary\n" + f"[[synthesis/{production.page_name(artefact)[:-3]}-summary]]\n"
            return metadata + "\n" + projection

        # In-process seam only, restored after the real ingest. No production file edits.
        with patch.object(production, "render_page", side_effect=render):
            report = production.ingest(self.wiki, AUTOPILOT)
        summary_bytes = self.summaries() if self.variant == "layered" else 0
        after = self.pages()
        return {"transitions": report["transitions"], "events": report["events"],
                "written_source_pages": report["written"], "summary_bytes_written": summary_bytes,
                "changed_files": sorted(p for p, text in after.items() if before.get(p) != text),
                "changed_file_bytes": sum(size(text)["bytes"] for p, text in after.items() if before.get(p) != text)}


def compare() -> dict:
    results = {}
    for variant in VARIANTS:
        with tempfile.TemporaryDirectory(prefix="SW01-PROTOTYPE-") as directory:
            experiment = Experiment(Path(directory), variant)
            first = experiment.run()
            pages = experiment.pages()
            measurements = []
            for fixture in FIXTURES:
                artefact = experiment.classify(fixture["path"])
                page = experiment.page_path(artefact.identity_key).read_text(encoding="utf-8")
                source_size, page_size = size(fixture["text"]), size(page)
                row = {"source": fixture["path"], "logical_kind": fixture["kind"],
                       "compiler_kind": artefact.kind, "identity": artefact.identity_key,
                       "weak_identity": artefact.weak_identity, "source_size": source_size,
                       "page_size": page_size,
                       "byte_ratio": round(page_size["bytes"] / source_size["bytes"], 4),
                       "word_ratio": round(page_size["words"] / source_size["words"], 4),
                       "questions": utility(page, fixture["answers"]),
                       "literal_fidelity": recover_preserved(page) == fixture["text"]
                       if variant in {"preserve", "layered"} else None}
                if variant == "layered":
                    summary = experiment.wiki / "wiki" / "synthesis" / (production.page_name(artefact)[:-3] + "-summary.md")
                    row["summary_questions"] = utility(summary.read_text(encoding="utf-8"), fixture["answers"])
                measurements.append(row)
            stat_before = {p: (experiment.wiki / p).stat().st_mtime_ns for p in pages}
            replay = experiment.run()
            unchanged_mtimes = all((experiment.wiki / p).stat().st_mtime_ns == stamp for p, stamp in stat_before.items())
            assert experiment.pages() == pages
            assert replay["written_source_pages"] == [] and replay["summary_bytes_written"] == 0
            assert unchanged_mtimes
            # A fresh directory, not merely the incremental skip branch, must replay identically.
            with tempfile.TemporaryDirectory(prefix="SW01-REPLAY-") as repeat:
                fresh = Experiment(Path(repeat), variant)
                fresh.run()
                deterministic = fresh.pages() == pages
                assert deterministic

            identity = "ticket:family/FX-01"
            original = experiment.page_path(identity).read_text(encoding="utf-8")
            source = FIXTURES[0]
            experiment.put(source["path"], source["text"].replace(LATE_FACT, EDITED_FACT))
            edit = experiment.run()
            edited = experiment.page_path(identity).read_text(encoding="utf-8")
            edit["semantic_body_changed"] = body(edited) != body(original)
            edit["new_fact_visible"] = EDITED_FACT in body(edited)
            edit["digest_changed"] = production.read_page_front_matter(experiment.page_path(identity))["source_digest"] != digest(source["text"])
            if variant == "layered":
                summary = experiment.wiki / "wiki" / "synthesis" / "ticket-family-fx-01-summary.md"
                edit["authored_summary_stale"] = "Freshness: stale" in summary.read_text(encoding="utf-8")

            old_page = experiment.page_path(identity).name
            destination = experiment.project / "docs/tickets/family/done/01.md"
            destination.parent.mkdir()
            (experiment.project / source["path"]).rename(destination)
            move = experiment.run()
            move["same_page_name"] = experiment.page_path(identity).name == old_page
            move["parent_link_preserved"] = "[[sources/artifact-fixture-map]]" in experiment.page_path(identity).read_text(encoding="utf-8")
            (experiment.project / "docs/research/forward.md").unlink()
            missing = experiment.run()
            missing["tombstone_retained"] = production.read_page_front_matter(experiment.page_path("artifact:fixture-research"))["source_status"] == "missing"
            final_replay = experiment.run()
            assert final_replay["changed_file_bytes"] == 0
            assert move["same_page_name"] and move["parent_link_preserved"] and missing["tombstone_retained"]

            broken_links = []
            for name, text in experiment.pages().items():
                for target in re.findall(r"\[\[((?:sources|synthesis)/[^\]|]+)(?:\|[^\]]+)?\]\]", text):
                    if not (experiment.wiki / "wiki" / (target + ".md")).is_file():
                        broken_links.append([name, target])
            assert not broken_links
            results[variant] = {"first": first, "measurements": measurements,
                "total_generated": size("".join(pages.values())), "pages": pages,
                "replay": replay, "unchanged_mtimes": unchanged_mtimes,
                "fresh_directory_deterministic": deterministic, "semantic_edit": edit,
                "disposition_move": move, "missing_source": missing,
                "final_replay": final_replay, "broken_wikilinks": broken_links}
    return {"prototype": True, "baseline": "6b8ea103d4e5bb0e188116984a64882c5d77e53e",
            "section_limit_characters": SECTION_LIMIT,
            "configured_globs": list(DEFAULT_DOCS_GLOBS), "fixture_only_extra_glob": "docs/guides/*.md",
            "source_manifest": [{"path": f["path"], "source": f["source"], "kind": f["kind"],
                                 "normalized_digest": digest(f["text"])} for f in FIXTURES],
            "variants": results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="retain all generated pages and measurements as JSON")
    args = parser.parse_args()
    result = compare()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {name: {k: v for k, v in data.items() if k != "pages"} for name, data in result["variants"].items()}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
