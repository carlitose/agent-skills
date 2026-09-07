"""Real filesystem/Git regressions; the provider below is injected, never live."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "llm-wiki/scripts"), str(ROOT / "ticket-autopilot/scripts")]
from scaffold import scaffold
from sync_project import sync_project
from autopilot import wiki_sync
from autopilot.kernel import TransitionError

support = importlib.import_module(
    f"{__package__}.test_wiki_sync" if __package__ else "test_wiki_sync"
)


def fixture_io(path: Path) -> Path:
    # Independent fixture setup/control, not the production adapter under test.
    return Path("\\\\?\\" + str(path.absolute())) if os.name == "nt" else path


class RecordingProvider(support.DeliveryGitHubRunner):
    def __init__(self) -> None:
        super().__init__()
        self.creates = 0
        self.calls = []

    def run(self, command: list[str], *, cwd: Path):
        self.calls.append(command[:])
        if command[:3] == ["gh", "pr", "create"]:
            self.creates += 1
        if command[:3] == ["gh", "api", "repos/{owner}/{repo}/pulls/73"]:
            assert command[3:5] == ["--method", "PATCH"]
            fields = dict(command[i + 1].split("=", 1) for i, value in enumerate(command) if value == "--raw-field")
            self.base, self.body = fields["base"], fields["body"]
            return support.CommandResult("{}", "", 0)
        return super().run(command, cwd=cwd)


class WikiLongPathTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="wl-" + ("posix-" * 6 if os.name != "nt" else ""))
        self.root = Path(temporary.name).resolve()
        temporary.name = str(fixture_io(self.root))
        self.addCleanup(temporary.cleanup)
        empty = self.root / "empty"
        empty.mkdir()
        config = self.root / "gitconfig"
        config.write_bytes(b"")
        attributes = self.root / "attributes"
        attributes.write_bytes(b"")
        environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        environment.update(GIT_CONFIG_GLOBAL=str(config), GIT_CONFIG_NOSYSTEM="1", GIT_ATTR_NOSYSTEM="1", GIT_TEMPLATE_DIR=str(empty), GIT_TERMINAL_PROMPT="0", GIT_DEFAULT_HASH="sha1")
        settings = {"user.name": "Wiki Path Test", "user.email": "test@example.invalid", "core.autocrlf": "false", "core.eol": "lf", "commit.gpgSign": "false", "tag.gpgSign": "false", "core.hooksPath": str(empty), "core.attributesFile": str(attributes)}
        environment["GIT_CONFIG_COUNT"] = str(len(settings))
        for index, (key, value) in enumerate(settings.items()):
            environment[f"GIT_CONFIG_KEY_{index}"] = key
            environment[f"GIT_CONFIG_VALUE_{index}"] = value
        patch = mock.patch.dict(os.environ, environment, clear=True)
        patch.start()
        self.addCleanup(patch.stop)

    def git(self, root: Path, *args: str) -> str:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True, text=True, encoding="utf-8", timeout=30).stdout.strip()

    def project(self, name: str = "p") -> Path:
        project = self.root / name
        (project / "docs/specs").mkdir(parents=True)
        (project / "docs/specs/artifact-graph-disposition-drift-diagnostic.md").write_bytes(b"# Diagnostic\n\nA local project decision.\n")
        scaffold(project / "knowledge", "Paths", project)
        self.git(project, "init", "--initial-branch=main")
        self.git(project, "add", ".")
        self.git(project, "commit", "-m", "project")
        self.git(project, "remote", "add", "origin", "https://github.com/example/paths.git")
        return project

    def snapshot(self, root: Path) -> dict[str, bytes]:
        native = fixture_io(root)
        return {p.relative_to(native).as_posix(): p.read_bytes() for p in native.rglob("*") if p.is_file() and ".git" not in p.relative_to(native).parts}

    def historical_candidate(self, project: Path) -> dict:
        result = support.frozen_candidate(project)
        old = Path(result["candidate_path"])
        relative = "wiki/sources/artifact-artifact-graph-disposition-drift-diagnostic.md"
        payload = fixture_io(old / relative)
        payload.parent.mkdir(parents=True)
        payload.write_bytes("# Long file\n\nDecisione à, prova β.\n".encode("utf-8"))
        entries = [{"path": p.relative_to(fixture_io(old)).as_posix(), "kind": "file", "mode": stat.S_IMODE(p.stat().st_mode), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(fixture_io(old).rglob("*.md"))]
        digest = wiki_sync._wiki_contract_digest(entries)
        destination = old.parent / digest
        fixture_io(old).rename(fixture_io(destination))
        result["candidate_path"] = str(destination)
        result["candidate_ref"]["candidate_tree_sha256"] = digest
        result["changed_paths"].append(relative)
        fixture_io(destination / "manifest.json").write_bytes((json.dumps({"candidate_ref": result["candidate_ref"], "validation_receipt": result["validation_receipt"]}, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))
        self.assertGreaterEqual(len(str(destination / relative)), 262)
        return result

    def test_native_historical_candidate_validation(self) -> None:
        project = self.project()
        result = self.historical_candidate(project)
        candidate = Path(result["candidate_path"])
        before = self.snapshot(candidate)
        long_file = candidate / result["changed_paths"][-1]
        if os.name == "nt":
            # The RED log records WinError 3 on the affected host. Newer hosts may
            # support ordinary long access; either way the real regular file must pass.
            try:
                observed = long_file.stat()
            except OSError as error:
                self.assertIn(error.winerror, (3, 206))
            else:
                self.assertTrue(stat.S_ISREG(observed.st_mode))
            self.assertTrue(stat.S_ISREG(fixture_io(long_file).lstat().st_mode))
        target, receipt = wiki_sync._delivery_target(project, result, provider_name="github")
        self.assertEqual(project, target)
        self.assertEqual("knowledge", receipt["wiki_relative"])
        files = wiki_sync._frozen_files(candidate, result)
        self.assertEqual(sorted(result["changed_paths"]), sorted(files))
        self.assertEqual(before, self.snapshot(candidate))
        self.assertNotIn("\\\\?\\", json.dumps([result, receipt]))

    def test_portable_exact_source_sync_to_git_delivery_and_readback(self) -> None:
        for name in ("s", "progetto à profondo", "deep/" + "segmento β" * 6):
            with self.subTest(name=name):
                project = self.project(name)
                head = self.git(project, "rev-parse", "HEAD")
                source = self.root / (name + " source β")
                self.git(project, "worktree", "add", "--detach", str(source), head)
                self.addCleanup(self.git, project, "worktree", "remove", str(source))
                remote = self.root / (name + " remote.git")
                self.git(self.root, "clone", "--bare", str(project), str(remote))
                # Local transport, canonical public identity; no live provider/network call.
                self.git(project, "config", "url." + str(remote) + ".insteadOf", "https://github.com/example/paths.git")
                protected = (self.snapshot(project), self.snapshot(source))
                self.assertEqual(project, wiki_sync._bound_project_target(project, source, provider_name="github"))
                result = sync_project(project, source_root=source, expected_source_head=head, autopilot_root=ROOT / "ticket-autopilot")
                self.assertEqual("candidate-created", result["status"], result)
                candidate = Path(result["candidate_path"])
                frozen = self.snapshot(candidate)
                repeated = sync_project(project, source_root=source, expected_source_head=head, autopilot_root=ROOT / "ticket-autopilot")
                self.assertEqual(result["candidate_path"], repeated["candidate_path"], repeated)
                self.assertEqual(result["candidate_ref"], repeated["candidate_ref"])
                wiki_sync._delivery_target(project, result, provider_name="github")
                runner = RecordingProvider()
                delivery = wiki_sync.deliver_tracked_candidate(project, result, base_branch="main", provider_name="github", provider_mode="live", runner=runner)
                self.assertEqual("pr-open", delivery["status"])
                for relative, payload in frozen.items():
                    if relative == "manifest.json":
                        continue
                    actual = subprocess.run(["git", "show", delivery["head_sha"] + ":knowledge/" + relative], cwd=project, capture_output=True, check=True, timeout=30).stdout
                    self.assertEqual(payload, actual)
                replay = wiki_sync.deliver_tracked_candidate(project, result, base_branch="main", provider_name="github", provider_mode="live", runner=runner)
                self.assertEqual(delivery["head_sha"], replay["head_sha"])
                self.assertEqual(1, runner.creates)
                self.assertEqual(frozen, self.snapshot(candidate))
                self.assertEqual(protected, (self.snapshot(project), self.snapshot(source)))
                self.assertEqual(head, self.git(project, "rev-parse", "HEAD"))
                self.assertEqual("", self.git(project, "status", "--porcelain"))
                self.assertNotIn("\\\\?\\", json.dumps([result, delivery, runner.body]))

    @unittest.skipUnless(os.name == "nt", "historical Win32 retry requires native Windows")
    def test_exact_historical_retry_is_revalidated_provider_free_and_idempotent(self) -> None:
        project = self.project()
        result = self.historical_candidate(project)
        head = self.git(project, "rev-parse", "HEAD")
        kernel = support.integrated_kernel(project, head)
        record = {"state": "terminal", "result": result, "delivery": {"schema": 1, "status": "failed", "reason": "delivery-invalid", "detail": "tracked wiki candidate contains a non-regular path", "retry": {"disposition": "terminal", "max_attempts": 1}}}
        kernel.ledger["tickets"]["01"]["delivery"]["wiki-sync"] = copy.deepcopy(record)
        store = support.MemoryStore(self.root)
        with mock.patch.object(wiki_sync, "ProviderExecutor", side_effect=AssertionError("retry must not reach provider")):
            status = wiki_sync.wiki_delivery_retry_status(project, kernel, "01")
            self.assertTrue(status["eligible"], status)
            kwargs = dict(expected_record_sha256=status["record_sha256"], actor="operator", evidence="session://long-path-retry")
            first = wiki_sync.retry_wiki_delivery(project, store, kernel, "01", **kwargs)
            replay = wiki_sync.retry_wiki_delivery(project, store, kernel, "01", **kwargs)
        self.assertEqual(first["receipt"], replay["receipt"])
        self.assertEqual(record, kernel.ledger["tickets"]["01"]["delivery"]["wiki-sync"]["delivery_retry"]["previous_record"])
        self.assertEqual("integrated", kernel.ledger["tickets"]["01"]["state"])
        # Applied replay is a no-op but may not claim a drifted predecessor is valid.
        path = fixture_io(Path(result["candidate_path"]) / result["changed_paths"][-1])
        path.write_bytes(path.read_bytes() + b"drift\n")
        before = copy.deepcopy(kernel.ledger)
        self.assertFalse(wiki_sync.wiki_delivery_retry_status(project, kernel, "01")["eligible"])
        with self.assertRaises(TransitionError):
            wiki_sync.retry_wiki_delivery(project, store, kernel, "01", **kwargs)
        self.assertEqual(before, kernel.ledger)

    def test_invalid_frozen_files_and_access_failures_remain_rejected(self) -> None:
        project = self.project()
        result = self.historical_candidate(project)
        candidate = Path(result["candidate_path"])
        path = fixture_io(candidate / result["changed_paths"][-1])
        payload = path.read_bytes()
        manifest = fixture_io(candidate / "manifest.json")
        manifest_bytes = manifest.read_bytes()
        for value, diagnostic in ((b"\xff", "not UTF-8"), (payload + b"drift", "tree hash")):
            with self.subTest(diagnostic=diagnostic):
                path.write_bytes(value)
                with self.assertRaisesRegex(TransitionError, diagnostic):
                    wiki_sync._delivery_target(project, result, provider_name="github")
        path.write_bytes(payload)
        path.unlink()
        with self.assertRaisesRegex(TransitionError, "tree hash"):
            wiki_sync._delivery_target(project, result, provider_name="github")
        path.write_bytes(payload)
        for value in (b"\xff", b"{", b"{}", manifest_bytes.replace(b"implementation-complete", b"production-ready")):
            manifest.write_bytes(value)
            with self.assertRaises(TransitionError):
                wiki_sync._delivery_target(project, result, provider_name="github")
        manifest.write_bytes(manifest_bytes)
        escaped = fixture_io(candidate / "outside.md")
        escaped.write_bytes(b"# outside\n")
        with self.assertRaisesRegex(TransitionError, "non-regular"):
            wiki_sync._delivery_target(project, result, provider_name="github")
        escaped.unlink()
        original_lstat = Path.lstat
        original_read = Path.read_bytes

        def inaccessible(value: Path, *args, **kwargs):
            if value == path:
                raise PermissionError("fixture denied")
            return original_lstat(value, *args, **kwargs)

        def unreadable(value: Path, *args, **kwargs):
            if value == path:
                raise PermissionError("fixture denied")
            return original_read(value, *args, **kwargs)

        for method, failure in (("lstat", inaccessible), ("read_bytes", unreadable)):
            with mock.patch.object(Path, method, failure):
                with self.assertRaisesRegex(TransitionError, "filesystem access failed"):
                    wiki_sync._delivery_target(project, result, provider_name="github")
        # A genuine directory replacing a file cannot satisfy the frozen digest.
        path.unlink()
        path.mkdir()
        with self.assertRaises(TransitionError):
            wiki_sync._delivery_target(project, result, provider_name="github")
        path.rmdir()
        path.write_bytes(payload)
        self.assertEqual(manifest_bytes, manifest.read_bytes())

    def test_manifest_receipt_access_error_is_a_delivery_rejection(self) -> None:
        project = self.project()
        result = self.historical_candidate(project)
        manifest = fixture_io(Path(result["candidate_path"]) / "manifest.json")
        original_read = Path.read_bytes

        def unreadable(path: Path):
            if path == manifest:
                raise PermissionError("fixture manifest denied")
            return original_read(path)

        with mock.patch.object(Path, "read_bytes", unreadable):
            with self.assertRaisesRegex(TransitionError, "manifest is unreadable"):
                wiki_sync._delivery_target(project, result, provider_name="github")

    def test_short_candidate_remains_valid(self) -> None:
        project = self.project()
        result = support.frozen_candidate(project)
        before = self.snapshot(Path(result["candidate_path"]))
        if os.name == "nt":
            self.assertLess(max(len(str(Path(result["candidate_path"]) / relative)) for relative in before), 260)
        wiki_sync._delivery_target(project, result, provider_name="github")
        self.assertEqual(before, self.snapshot(Path(result["candidate_path"])))

    @unittest.skipUnless(os.name == "nt", "native directory junction requires Windows")
    def test_directory_junction_is_not_followed(self) -> None:
        project = self.project()
        result = self.historical_candidate(project)
        target = self.root / "outside"
        target.mkdir()
        (target / "external.md").write_bytes(b"# external\n")
        link = Path(result["candidate_path"]) / "wiki/junction"
        observed = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)], capture_output=True, timeout=30)
        if observed.returncode:
            self.skipTest("native junction unavailable: " + repr(observed.stderr))
        self.addCleanup(fixture_io(link).rmdir)
        self.assertTrue(fixture_io(link).is_junction())
        with self.assertRaisesRegex(TransitionError, "non-regular"):
            wiki_sync._delivery_target(project, result, provider_name="github")
        self.assertEqual(b"# external\n", (target / "external.md").read_bytes())

    def test_symlinks_are_not_followed(self) -> None:
        project = self.project()
        result = self.historical_candidate(project)
        candidate = Path(result["candidate_path"])
        target = self.root / "outside.md"
        target.write_bytes(b"# external\n")
        link = fixture_io(candidate / "wiki/link.md")
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError) as error:
            self.skipTest("symbolic links unavailable: " + str(error))
        with self.assertRaisesRegex(TransitionError, "non-regular"):
            wiki_sync._delivery_target(project, result, provider_name="github")
        self.assertEqual(b"# external\n", target.read_bytes())

    @unittest.skipUnless(os.name != "nt", "native executable file modes require POSIX")
    def test_executable_and_fifo_are_not_regular_candidates(self) -> None:
        project = self.project()
        result = self.historical_candidate(project)
        path = Path(result["candidate_path"]) / result["changed_paths"][-1]
        path.chmod(0o755)
        with self.assertRaisesRegex(TransitionError, "non-regular"):
            wiki_sync._delivery_target(project, result, provider_name="github")
        path.unlink()
        os.mkfifo(path)
        with self.assertRaisesRegex(TransitionError, "non-regular"):
            wiki_sync._delivery_target(project, result, provider_name="github")

    @unittest.skipUnless(os.name == "nt", "historical Win32 retry requires native Windows")
    def test_retry_rejects_drift_authority_and_prior_provider_state_without_effects(self) -> None:
        project = self.project()
        result = self.historical_candidate(project)
        kernel = support.integrated_kernel(project, self.git(project, "rev-parse", "HEAD"))
        record = {"state": "terminal", "result": result, "delivery": {"schema": 1, "status": "failed", "reason": "delivery-invalid", "detail": "tracked wiki candidate contains a non-regular path", "retry": {"disposition": "terminal", "max_attempts": 1}}}
        baseline = copy.deepcopy(kernel.ledger)
        variants = []
        for key in ("authorization", "publication_authorization", "delivery_target", "delivery_retry"):
            variants.append({**copy.deepcopy(record), key: {"prior": "state"}})
        for update in ({"pr_id": "73"}, {"status": "pr-open"}, {"detail": []}, {"detail": "prefix: tracked wiki candidate contains a non-regular path"}, {"reason": "provider-unknown"}):
            changed = copy.deepcopy(record)
            changed["delivery"].update(update)
            variants.append(changed)
        for key, value in (("candidate_path", str(self.root)), ("wiki_identity", str(self.root)), ("candidate_path", str(fixture_io(Path(result["candidate_path"]))))):
            changed = copy.deepcopy(record)
            changed["result"][key] = value
            variants.append(changed)
        for changed in variants:
            kernel.ledger = copy.deepcopy(baseline)
            kernel.ledger["tickets"]["01"]["delivery"]["wiki-sync"] = changed
            before = copy.deepcopy(kernel.ledger)
            store = support.MemoryStore(self.root)
            with mock.patch.object(wiki_sync, "ProviderExecutor", side_effect=AssertionError("provider forbidden")):
                self.assertFalse(wiki_sync.wiki_delivery_retry_status(project, kernel, "01")["eligible"])
                with self.assertRaises(TransitionError):
                    wiki_sync.retry_wiki_delivery(project, store, kernel, "01", expected_record_sha256=wiki_sync._digest(changed), actor="operator", evidence="session://retry")
            self.assertEqual(before, kernel.ledger)
            self.assertEqual([], store.saved)
        kernel.ledger = copy.deepcopy(baseline)
        kernel.ledger["tickets"]["01"]["delivery"]["wiki-sync"] = copy.deepcopy(record)
        for digest, actor, evidence in (("0" * 64, "operator", "session://retry"), (wiki_sync._digest(record), "", "session://retry"), (wiki_sync._digest(record), "operator", "")):
            store = support.MemoryStore(self.root)
            with self.assertRaises(TransitionError):
                wiki_sync.retry_wiki_delivery(project, store, kernel, "01", expected_record_sha256=digest, actor=actor, evidence=evidence)
            self.assertEqual([], store.saved)

    def test_native_spelling_and_binary_hash_boundary(self) -> None:
        from wiki_io import _windows_io_spelling, native_path
        for raw, expected in (("C:\\project à\\wiki\\x.md", "\\\\?\\C:\\project à\\wiki\\x.md"), ("\\\\server\\share\\wiki β\\x.md", "\\\\?\\UNC\\server\\share\\wiki β\\x.md"), ("\\\\?\\C:\\already\\x.md", "\\\\?\\C:\\already\\x.md")):
            self.assertEqual(expected, _windows_io_spelling(raw))
        if os.name != "nt":
            literal = Path("literal\\backslash.md")
            self.assertEqual(literal, native_path(literal))
        project = self.project()
        path = self.root / "bytes.md"
        payload = "# Dati à\r\n\nSpazi β  \n".encode("utf-8")
        path.write_bytes(payload)
        expected = hashlib.sha1(b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload).hexdigest()
        self.assertEqual(expected, wiki_sync._hash_frozen_blob(project, path))
        absent = subprocess.run(["git", "cat-file", "-e", expected], cwd=project, capture_output=True, timeout=30)
        self.assertNotEqual(0, absent.returncode, "hash-object must not write an object")
        self.assertEqual(payload, path.read_bytes())
        for observed in (subprocess.CompletedProcess([], 0, b"\xff", b""), subprocess.CompletedProcess([], 0, b"not-an-oid", b""), subprocess.CompletedProcess([], 1, b"", b"failure")):
            with mock.patch.object(wiki_sync.subprocess, "run", return_value=observed) as process:
                with self.assertRaises(wiki_sync.GitError):
                    wiki_sync._hash_frozen_blob(project, path)
                args, kwargs = process.call_args
                self.assertEqual(["git", "hash-object", "--stdin", "--no-filters"], args[0])
                self.assertEqual(payload, kwargs["input"])
                self.assertEqual(30, kwargs["timeout"])
        with mock.patch.object(wiki_sync.subprocess, "run", side_effect=subprocess.TimeoutExpired("git", 30)):
            with self.assertRaises(wiki_sync.GitError):
                wiki_sync._hash_frozen_blob(project, path)


if __name__ == "__main__":
    unittest.main()
