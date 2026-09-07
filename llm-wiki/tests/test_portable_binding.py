from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "llm-wiki/scripts"))
sys.path.insert(0, str(ROOT / "ticket-autopilot/scripts"))

from project_binding import BindingError, config_path, discover_artefacts, read_binding, resolve_project_root, write_binding
from scaffold import scaffold
from sync_project import sync_project
import sync_project as sync_module
from lint_drift import Page, check_session_pointers
from autopilot.kernel import TransitionError
from autopilot.wiki_sync import _bound_project_target, _delivery_target


class PortableBindingIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="pw-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        empty = self.base / "empty"
        empty.mkdir()
        config = self.base / "gitconfig"
        config.write_bytes(b"")
        attributes = self.base / "attributes"
        attributes.write_bytes(b"")
        environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        environment.update(GIT_CONFIG_GLOBAL=str(config), GIT_CONFIG_NOSYSTEM="1", GIT_ATTR_NOSYSTEM="1", GIT_TEMPLATE_DIR=str(empty), GIT_TERMINAL_PROMPT="0", GIT_DEFAULT_HASH="sha1")
        settings = {
            "user.name": "Portable Wiki Test", "user.email": "test@example.invalid",
            "core.autocrlf": "false", "core.eol": "lf", "commit.gpgSign": "false",
            "tag.gpgSign": "false", "core.hooksPath": str(empty), "core.attributesFile": str(attributes),
        }
        environment["GIT_CONFIG_COUNT"] = str(len(settings))
        for index, (key, value) in enumerate(settings.items()):
            environment[f"GIT_CONFIG_KEY_{index}"] = key
            environment[f"GIT_CONFIG_VALUE_{index}"] = value
        patch = mock.patch.dict(os.environ, environment, clear=True)
        patch.start()
        self.addCleanup(patch.stop)
        previous = Path.cwd()
        foreign = self.base / "unrelated cwd"
        foreign.mkdir()
        os.chdir(foreign)
        self.addCleanup(os.chdir, previous)

    def git(self, root: Path, *args: str) -> str:
        return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True, encoding="utf-8", timeout=30).stdout.strip()

    def seed(self, layout: str = "knowledge") -> Path:
        project = self.base / "seed"
        (project / "docs/specs").mkdir(parents=True)
        (project / "docs/specs/local.md").write_bytes(b"# Local\n\nA project decision.\n")
        wiki = project / layout
        scaffold(wiki, "Portable", project)
        (wiki / "wiki/sources/session-ref.md").write_bytes((
            "---\nkind: ref\nprovider: claude-code\nsession_id: absent\n"
            f"external_path: {(self.base / 'unavailable-machine/session.jsonl').as_posix()}\n"
            "size_bytes: 10\nrecord_count: 1\n---\n\n# Unavailable session\n\nLocal transcript provenance only.\n"
        ).encode("utf-8"))
        self.git(project, "init", "--initial-branch=main")
        self.git(project, "add", ".")
        self.git(project, "commit", "-m", "portable project")
        self.git(project, "remote", "add", "origin", "https://github.com/example/portable.git")
        return project.resolve()

    def snapshot(self, root: Path) -> dict[str, bytes]:
        return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts}

    def check_candidate(self, project: Path, source: Path, layout: str, head: str) -> dict:
        wiki = source / layout
        protected = (self.snapshot(project), self.snapshot(source))
        result = sync_project(project, autopilot_root=ROOT / "ticket-autopilot", source_root=source, expected_source_head=head)
        self.assertEqual("candidate-created", result["status"], result)
        self.assertEqual(str(project / layout), result["wiki_identity"])
        common = Path(self.git(project, "rev-parse", "--path-format=absolute", "--git-common-dir"))
        candidate = Path(result["candidate_path"])
        self.assertTrue(candidate.is_relative_to(common / "llm-wiki/candidates"))
        self.assertEqual(protected, (self.snapshot(project), self.snapshot(source)))
        self.assertEqual("", self.git(project, "status", "--porcelain"))
        self.assertEqual("", self.git(source, "status", "--porcelain"))
        self.assertEqual(head, self.git(source, "rev-parse", "HEAD"))
        pages = list((candidate / "wiki/sources").glob("*.md"))
        self.assertTrue(any("source_path: docs/specs/local.md" in p.read_text(encoding="utf-8") for p in pages))
        self.assertFalse(any("llm-wiki-sync-" in p.read_text(encoding="utf-8") for p in pages))
        receipt = result["validation_receipt"]
        lint = next(check for check in receipt["checks"] if check["id"] == "llm-wiki-lint")
        pointer_pass = next(item for item in lint["passes"] if item["pass"] == "stale-session-pointer")
        self.assertEqual(("warning", 1), (pointer_pass["severity"], pointer_pass["issues"]))
        pointer = check_session_pointers(candidate, [Page(p, candidate) for p in pages])
        self.assertIn("is gone", pointer.issues[0])
        self.assertEqual(".." if layout == "knowledge" else ".", read_binding(wiki)["project_root"])
        return result

    def test_independent_clones_and_relocation_use_identical_binding_bytes(self) -> None:
        seed = self.seed()
        raw = config_path(seed / "knowledge").read_bytes()
        # Local authority belongs to this Git common directory, never the commit.
        authority = seed / ".git/ticket-autopilot/authority-sentinel"
        authority.parent.mkdir(parents=True)
        authority.write_bytes(b"local-only")
        # Keep this binding test below MAX_PATH; APM-11 owns long-path I/O.
        for name in ("a à", "b β"):
            clone = self.base / name
            self.git(self.base, "clone", "--no-local", str(seed), str(clone))
            self.git(clone, "remote", "set-url", "origin", "https://github.com/example/portable.git")
            if name.endswith("β"):
                clone = clone.rename(self.base / "c β")
            with self.subTest(clone=clone):
                self.assertEqual(raw, config_path(clone / "knowledge").read_bytes())
                self.assertEqual(clone, resolve_project_root(clone / "knowledge"))
                self.assertEqual(["docs/specs/local.md"], discover_artefacts(clone / "knowledge"))
                self.assertFalse((clone / ".git/ticket-autopilot/authority-sentinel").exists())
                self.assertEqual(clone, _bound_project_target(clone, clone, provider_name="github"))
                self.check_candidate(clone, clone, "knowledge", self.git(clone, "rev-parse", "HEAD"))
                self.assertEqual(raw, config_path(clone / "knowledge").read_bytes())

    def test_exact_source_uses_canonical_owner_without_a_materialized_wiki(self) -> None:
        project = self.seed()
        integrated = self.git(project, "rev-parse", "HEAD")
        source = self.base / "source à"
        self.git(project, "worktree", "add", "--detach", str(source), integrated)
        self.addCleanup(self.git, project, "worktree", "remove", str(source))
        self.git(project, "rm", "-r", "knowledge")
        self.git(project, "commit", "-m", "canonical checkout lacks wiki")
        canonical_head = self.git(project, "rev-parse", "HEAD")
        self.assertEqual(project, _bound_project_target(project, source, provider_name="github"))
        result = self.check_candidate(project, source, "knowledge", integrated)
        self.assertFalse((project / "knowledge/llm-wiki-project.json").exists())
        self.assertEqual(canonical_head, self.git(project, "rev-parse", "HEAD"))
        self.assertEqual(str(project), result["wiki_sync_ref"]["project_root"])
        stale = sync_project(project, source_root=source, expected_source_head=canonical_head)
        self.assertEqual(("failed", "stale-tree"), (stale["status"], stale["reason"]))
        clone = self.base / "independent same remote"
        self.git(self.base, "clone", "--no-local", str(project), str(clone))
        self.git(clone, "remote", "set-url", "origin", "https://github.com/example/portable.git")
        wrong_common = sync_project(clone, source_root=source, expected_source_head=integrated)
        self.assertEqual(("failed", "broken-binding"), (wrong_common["status"], wrong_common["reason"]))

    def test_root_level_binding_sync_and_runner_target(self) -> None:
        project = self.seed(".")
        self.assertEqual(".", read_binding(project)["project_root"])
        self.assertEqual(project, _bound_project_target(project, project, provider_name="github"))
        result = self.check_candidate(project, project, ".", self.git(project, "rev-parse", "HEAD"))
        target, receipt = _delivery_target(project, result, provider_name="github")
        self.assertEqual(project, target)
        self.assertEqual(".", receipt["wiki_relative"])
        self.assertTrue(all(path.startswith("wiki/") and path.endswith(".md") for path in result["changed_paths"]))

    def test_compile_cannot_hide_binding_changes_with_restoration(self) -> None:
        project = self.seed()
        protected = self.snapshot(project)
        ingest = sync_module.ingest_docs

        def tamper(stage: Path, autopilot: Path) -> dict:
            report = ingest(stage, autopilot)
            document = read_binding(stage)
            document["auto_sync"] = "disabled"
            config_path(stage).write_bytes(json.dumps(document).encode("utf-8"))
            return report

        with mock.patch.object(sync_module, "ingest_docs", side_effect=tamper):
            result = sync_project(project, autopilot_root=ROOT / "ticket-autopilot")
        self.assertEqual(("failed", "forbidden-scope"), (result["status"], result["reason"]))
        self.assertEqual(protected, self.snapshot(project))
        self.assertEqual("", self.git(project, "status", "--porcelain"))

    def test_missing_malformed_and_wrong_layout_fail_without_rebinding(self) -> None:
        project = self.seed()
        wiki = project / "knowledge"
        original = read_binding(wiki)
        other = self.base / "other"
        other.mkdir()
        for value in ("missing", "", None, "\x00", str(self.base / "absent")):
            with self.subTest(value=value):
                document = {**original, "project_root": value}
                config_path(wiki).write_bytes(json.dumps(document).encode("utf-8"))
                with self.assertRaises(BindingError):
                    resolve_project_root(wiki)
        config_path(wiki).write_bytes(json.dumps({**original, "project_root": "."}).encode("utf-8"))
        with self.assertRaisesRegex(BindingError, "not internal"):
            resolve_project_root(wiki, source_root=project, target_root=other)
        with self.assertRaises(TransitionError):
            _bound_project_target(project, project, provider_name="github")
        config_path(wiki).write_bytes(b"\xff")
        with self.assertRaises(BindingError):
            resolve_project_root(wiki)
        # Absolute bindings stay literal even when source/target mapping is offered.
        config_path(wiki).write_bytes(json.dumps({**original, "project_root": str(other)}).encode("utf-8"))
        self.assertEqual(other, resolve_project_root(wiki, source_root=project, target_root=project))


if __name__ == "__main__":
    unittest.main()
