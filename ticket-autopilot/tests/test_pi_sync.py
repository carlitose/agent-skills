from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "ticket-autopilot" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.git_ops import CommandResult
from autopilot.pi_sync import (
    PiSyncError,
    PiSyncRequest,
    PiSyncTransaction,
    _digest,
    _local_source_matches_checkout,
    _pi_list_checkout_count,
    _pi_list_package_sources,
    _reconcile_settings,
    integrated_pi_sync_binding,
)


GIT_SOURCE = "git:github.com/carlitose/agent-skills@" + "a" * 40


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.strip()


def write_skill(root: Path, name: str, value: str) -> None:
    folder = root / name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "SKILL.md").write_text(
        f'---\nname: "{name}"\ndescription: "{value}"\n---\n\n# {name}\n',
        encoding="utf-8",
    )
    (folder / "payload.txt").write_text(value + "\n", encoding="utf-8")


def commit(root: Path, message: str) -> tuple[str, str]:
    git(root, "add", "-A")
    git(root, "commit", "-m", message)
    head = git(root, "rev-parse", "HEAD")
    return head, git(root, "rev-parse", "HEAD^{tree}")


class FakePiRunner:
    def __init__(self, settings: Path):
        self.settings = settings
        self.install_calls = 0
        self.list_calls = 0
        self.commands: list[list[str]] = []
        self.fail_install = False
        self.bad_list = False
        self.wrong_install_source = False

    def run(self, command: list[str], *, cwd: Path) -> CommandResult:
        self.commands.append(list(command))
        if command[:3] == [
            "zsh",
            "-lic",
            'PI_CODING_AGENT_DIR="$1" pi install "$2"',
        ]:
            self.install_calls += 1
            if self.fail_install:
                return CommandResult("", "simulated install failure", 1)
            if command[-2] != self.settings.parent.as_posix():
                return CommandResult("", "wrong Pi config directory", 2)
            checkout = Path(command[-1])
            settings_root = Path(command[-2])
            document = json.loads(self.settings.read_text(encoding="utf-8"))
            if not any(
                _local_source_matches_checkout(
                    entry if isinstance(entry, str) else entry.get("source"),
                    checkout,
                    settings_root,
                )
                for entry in document["packages"]
            ):
                source = (
                    "local/not-agent-skills"
                    if self.wrong_install_source
                    else os.path.relpath(checkout, settings_root)
                )
                document["packages"].append(source)
            self.settings.write_text(json.dumps(document), encoding="utf-8")
            return CommandResult("installed\n", "", 0)
        if command[:3] == [
            "zsh", "-lic", 'PI_CODING_AGENT_DIR="$1" pi list'
        ]:
            self.list_calls += 1
            if command[-1] != self.settings.parent.as_posix():
                return CommandResult("", "wrong Pi config directory", 2)
            if self.bad_list:
                return CommandResult("User packages:\n", "", 0)
            document = json.loads(self.settings.read_text(encoding="utf-8"))
            sources = [
                entry if isinstance(entry, str) else entry.get("source")
                for entry in document["packages"]
            ]
            rows = []
            for source in sources:
                rows.append(f"  {source}\n")
                if _local_source_matches_checkout(
                    source, cwd, self.settings.parent
                ):
                    rows.append(f"    {cwd.as_posix()}\n")
            return CommandResult("User packages:\n" + "".join(rows), "", 0)
        return CommandResult("", "unexpected command", 1)


class Fixture:
    def __init__(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.source = self.root / "source"
        self.checkout = self.root / "pi" / "local" / "agent-skills"
        self.agents = self.root / "agents" / "skills"
        self.settings = self.root / "pi" / "settings.json"
        self.state = self.root / "state" / "sync.json"
        self.source.mkdir()
        git(self.source, "init", "-b", "main")
        git(self.source, "config", "user.name", "Test")
        git(self.source, "config", "user.email", "test@example.com")
        (self.source / "package.json").write_text(
            json.dumps(
                {
                    "name": "carlitose-agent-skills-pi",
                    "pi": {
                        "extensions": ["./extensions/mandatory-agent-skills.ts"],
                        "skills": ["./*/SKILL.md"],
                    },
                }
            ),
            encoding="utf-8",
        )
        write_skill(self.source, "alpha", "one")
        write_skill(self.source, "beta", "two")
        self.head, self.tree = commit(self.source, "initial")
        self.agents.mkdir(parents=True)
        write_skill(self.agents, "alpha", "old")
        write_skill(self.agents, "external", "keep")
        self.settings.parent.mkdir(parents=True, exist_ok=True)
        self.settings.write_text(
            json.dumps(
                {
                    "theme": "dark",
                    "packages": [
                        "npm:other",
                        {"source": GIT_SOURCE, "skills": []},
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.runner = FakePiRunner(self.settings)

    def request(
        self,
        *,
        head: str | None = None,
        tree: str | None = None,
        adopt: bool = True,
        replace: bool = True,
    ) -> PiSyncRequest:
        return PiSyncRequest.normalize(
            source_repository=str(self.source),
            expected_head=head or self.head,
            expected_tree=tree or self.tree,
            checkout=str(self.checkout),
            agents_root=str(self.agents),
            settings_path=str(self.settings),
            actor="carlo",
            evidence="decision://pi-sync",
            adopt_existing_owned=adopt,
            replace_package_source=replace,
        )

    def close(self) -> None:
        self.temporary.cleanup()


class PiSyncTests(unittest.TestCase):
    def test_first_sync_preserves_external_skills_and_migrates_one_filtered_package(self) -> None:
        fixture = Fixture()
        try:
            settings_before = hashlib.sha256(fixture.settings.read_bytes()).hexdigest()
            result = PiSyncTransaction(runner=fixture.runner).apply(
                fixture.request(), state_path=fixture.state
            )
            settings = json.loads(fixture.settings.read_text(encoding="utf-8"))
            manifest = json.loads(
                (fixture.agents / ".agent-skills-install-manifest.json").read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual("completed", result["status"])
            self.assertFalse(result["replayed"])
            self.assertTrue(result["reload_required"])
            self.assertEqual(
                settings_before, result["receipt"]["settings_before_digest"]
            )
            self.assertEqual(
                hashlib.sha256(fixture.settings.read_bytes()).hexdigest(),
                result["receipt"]["settings_after_digest"],
            )
            self.assertEqual(
                ["Active Pi session was not reloaded; /reload is required."],
                result["receipt"]["limitations"],
            )
            self.assertEqual("one\n", (fixture.agents / "alpha" / "payload.txt").read_text())
            self.assertEqual("two\n", (fixture.agents / "beta" / "payload.txt").read_text())
            self.assertEqual("keep\n", (fixture.agents / "external" / "payload.txt").read_text())
            self.assertEqual({"alpha", "beta"}, set(manifest["skills"]))
            self.assertEqual("dark", settings["theme"])
            self.assertEqual("npm:other", settings["packages"][0])
            self.assertEqual(
                {"source": "local/agent-skills", "skills": []},
                settings["packages"][1],
            )
            self.assertEqual(1, fixture.runner.install_calls)
            self.assertEqual(
                [
                    "zsh",
                    "-lic",
                    'PI_CODING_AGENT_DIR="$1" pi install "$2"',
                    "agent-skills-pi-sync",
                    fixture.settings.parent.as_posix(),
                    fixture.checkout.as_posix(),
                ],
                fixture.runner.commands[0],
            )
            self.assertFalse(any("pi update" in " ".join(command) for command in fixture.runner.commands))
        finally:
            fixture.close()

    def test_existing_absolute_local_source_completes_without_duplicate(self) -> None:
        fixture = Fixture()
        try:
            settings = json.loads(fixture.settings.read_text(encoding="utf-8"))
            settings["packages"][1] = {
                "source": fixture.checkout.as_posix(),
                "skills": [],
            }
            fixture.settings.write_text(json.dumps(settings), encoding="utf-8")

            result = PiSyncTransaction(runner=fixture.runner).apply(
                fixture.request(replace=False), state_path=fixture.state
            )
            packages = json.loads(
                fixture.settings.read_text(encoding="utf-8")
            )["packages"]
            self.assertEqual("completed", result["status"])
            self.assertEqual(1, fixture.runner.install_calls)
            self.assertEqual(
                {"source": fixture.checkout.as_posix(), "skills": []},
                packages[1],
            )
            self.assertEqual(
                1,
                sum(
                    _local_source_matches_checkout(
                        entry if isinstance(entry, str) else entry.get("source"),
                        fixture.checkout,
                        fixture.settings.parent,
                    )
                    for entry in packages
                ),
            )
        finally:
            fixture.close()

    def test_exact_replay_reobserves_without_second_install_or_duplicate(self) -> None:
        fixture = Fixture()
        try:
            transaction = PiSyncTransaction(runner=fixture.runner)
            first = transaction.apply(fixture.request(), state_path=fixture.state)
            settings_bytes = fixture.settings.read_bytes()
            second = transaction.apply(fixture.request(), state_path=fixture.state)

            self.assertFalse(first["replayed"])
            self.assertTrue(second["replayed"])
            self.assertEqual(1, fixture.runner.install_calls)
            self.assertEqual(settings_bytes, fixture.settings.read_bytes())
            settings = json.loads(settings_bytes)
            self.assertEqual(
                1,
                sum(
                    _local_source_matches_checkout(
                        entry if isinstance(entry, str) else entry.get("source"),
                        fixture.checkout,
                        fixture.settings.parent,
                    )
                    for entry in settings["packages"]
                ),
            )
            (fixture.agents / "alpha" / "payload.txt").write_text("tampered\n")
            with self.assertRaisesRegex(PiSyncError, "installed skill drifted"):
                transaction.apply(fixture.request(), state_path=fixture.state)
            self.assertEqual(1, fixture.runner.install_calls)
        finally:
            fixture.close()

    def test_second_head_updates_adds_and_removes_only_previously_owned_skills(self) -> None:
        fixture = Fixture()
        try:
            PiSyncTransaction(runner=fixture.runner).apply(
                fixture.request(), state_path=fixture.state
            )
            (fixture.source / "alpha" / "payload.txt").write_text("new\n")
            for path in sorted((fixture.source / "beta").rglob("*"), reverse=True):
                path.unlink() if path.is_file() else path.rmdir()
            (fixture.source / "beta").rmdir()
            write_skill(fixture.source, "gamma", "three")
            head, tree = commit(fixture.source, "advance")
            next_state = fixture.root / "state" / f"{head}.json"

            PiSyncTransaction(runner=fixture.runner).apply(
                fixture.request(head=head, tree=tree, replace=False), state_path=next_state
            )

            self.assertEqual("new\n", (fixture.agents / "alpha" / "payload.txt").read_text())
            self.assertFalse((fixture.agents / "beta").exists())
            self.assertEqual("three\n", (fixture.agents / "gamma" / "payload.txt").read_text())
            self.assertEqual("keep\n", (fixture.agents / "external" / "payload.txt").read_text())
        finally:
            fixture.close()

    def test_unowned_collision_and_unauthorized_package_migration_fail_closed(self) -> None:
        fixture = Fixture()
        try:
            before = (fixture.agents / "alpha" / "payload.txt").read_bytes()
            with self.assertRaisesRegex(PiSyncError, "ownership proof"):
                PiSyncTransaction(runner=fixture.runner).apply(
                    fixture.request(adopt=False), state_path=fixture.state
                )
            self.assertEqual(before, (fixture.agents / "alpha" / "payload.txt").read_bytes())
            self.assertEqual(0, fixture.runner.install_calls)

            second = fixture.root / "state-2" / "sync.json"
            with self.assertRaisesRegex(PiSyncError, "replacement was not authorized"):
                PiSyncTransaction(runner=fixture.runner).apply(
                    fixture.request(replace=False), state_path=second
                )
        finally:
            fixture.close()

    def test_pi_failure_rolls_back_owned_skills_manifest_and_settings(self) -> None:
        fixture = Fixture()
        try:
            before_settings = fixture.settings.read_bytes()
            before_alpha = (fixture.agents / "alpha" / "payload.txt").read_bytes()
            fixture.runner.fail_install = True
            with self.assertRaisesRegex(PiSyncError, "simulated install failure"):
                PiSyncTransaction(runner=fixture.runner).apply(
                    fixture.request(), state_path=fixture.state
                )

            self.assertEqual(before_settings, fixture.settings.read_bytes())
            self.assertEqual(before_alpha, (fixture.agents / "alpha" / "payload.txt").read_bytes())
            self.assertFalse((fixture.agents / "beta").exists())
            self.assertFalse((fixture.agents / ".agent-skills-install-manifest.json").exists())
            self.assertEqual("keep\n", (fixture.agents / "external" / "payload.txt").read_text())
            self.assertEqual([], list(fixture.agents.glob(".agent-skills-pi-sync-*")))
        finally:
            fixture.close()

    def test_exact_failed_readback_state_retries_without_retargeting_intent(self) -> None:
        fixture = Fixture()
        try:
            before = fixture.settings.read_bytes()
            fixture.runner.wrong_install_source = True
            with self.assertRaisesRegex(PiSyncError, "exactly one local"):
                PiSyncTransaction(runner=fixture.runner).apply(
                    fixture.request(), state_path=fixture.state
                )
            failed = json.loads(fixture.state.read_text(encoding="utf-8"))["payload"]
            intent = failed["intent"]
            self.assertEqual(
                [
                    "intent-persisted",
                    "checkout-materialized",
                    "skills-replaced",
                    "pi-install-observed",
                ],
                failed["phases"],
            )
            self.assertEqual(before, fixture.settings.read_bytes())

            fixture.runner.wrong_install_source = False
            result = PiSyncTransaction(runner=fixture.runner).apply(
                fixture.request(), state_path=fixture.state
            )
            completed = json.loads(fixture.state.read_text(encoding="utf-8"))["payload"]
            self.assertEqual("completed", result["status"])
            self.assertEqual(intent, completed["intent"])
            self.assertEqual(2, fixture.runner.install_calls)
            self.assertEqual(
                {"source": "local/agent-skills", "skills": []},
                json.loads(fixture.settings.read_text(encoding="utf-8"))["packages"][1],
            )
        finally:
            fixture.close()

    def test_crash_after_skill_replacement_recovers_from_persisted_intent(self) -> None:
        fixture = Fixture()
        try:
            fired = False

            def crash(phase: str) -> None:
                nonlocal fired
                if phase == "skills-replaced" and not fired:
                    fired = True
                    raise SystemExit("simulated crash")

            with self.assertRaisesRegex(SystemExit, "simulated crash"):
                PiSyncTransaction(runner=fixture.runner, fault=crash).apply(
                    fixture.request(), state_path=fixture.state
                )
            result = PiSyncTransaction(runner=fixture.runner).apply(
                fixture.request(), state_path=fixture.state
            )

            self.assertEqual("completed", result["status"])
            self.assertEqual("one\n", (fixture.agents / "alpha" / "payload.txt").read_text())
            self.assertEqual("keep\n", (fixture.agents / "external" / "payload.txt").read_text())
            self.assertEqual([], list(fixture.agents.glob(".agent-skills-pi-sync-*")))
        finally:
            fixture.close()

    def test_symlinked_source_and_bad_list_readback_never_complete(self) -> None:
        fixture = Fixture()
        try:
            (fixture.source / "alpha" / "escape").symlink_to(fixture.root / "outside")
            head, tree = commit(fixture.source, "add unsafe link")
            with self.assertRaisesRegex(PiSyncError, "symlink or special file"):
                PiSyncTransaction(runner=fixture.runner).apply(
                    fixture.request(head=head, tree=tree), state_path=fixture.state
                )
            self.assertEqual(0, fixture.runner.install_calls)

            git(fixture.source, "rm", "alpha/escape")
            git(
                fixture.source,
                "update-index",
                "--add",
                "--cacheinfo",
                f"160000,{fixture.head},nested-submodule",
            )
            git(fixture.source, "commit", "-m", "add unsafe submodule")
            head = git(fixture.source, "rev-parse", "HEAD")
            tree = git(fixture.source, "rev-parse", "HEAD^{tree}")
            with self.assertRaisesRegex(PiSyncError, "submodule"):
                PiSyncTransaction(runner=fixture.runner).apply(
                    fixture.request(head=head, tree=tree),
                    state_path=fixture.root / "submodule-state" / "sync.json",
                )
            self.assertEqual(0, fixture.runner.install_calls)
        finally:
            fixture.close()

        fixture = Fixture()
        try:
            before = fixture.settings.read_bytes()
            fixture.runner.bad_list = True
            with self.assertRaisesRegex(PiSyncError, "pi list"):
                PiSyncTransaction(runner=fixture.runner).apply(
                    fixture.request(), state_path=fixture.state
                )
            self.assertEqual(before, fixture.settings.read_bytes())
            self.assertEqual("old\n", (fixture.agents / "alpha" / "payload.txt").read_text())
        finally:
            fixture.close()

    def test_wrong_tree_dirty_checkout_and_forged_completion_fail_closed(self) -> None:
        fixture = Fixture()
        try:
            before = (fixture.agents / "alpha" / "payload.txt").read_bytes()
            with self.assertRaisesRegex(PiSyncError, "commit or tree"):
                PiSyncTransaction(runner=fixture.runner).apply(
                    fixture.request(tree="b" * 40),
                    state_path=fixture.root / "wrong-state" / "sync.json",
                )
            self.assertEqual(before, (fixture.agents / "alpha" / "payload.txt").read_bytes())

            PiSyncTransaction(runner=fixture.runner).apply(
                fixture.request(), state_path=fixture.state
            )
            (fixture.checkout / "dirty.txt").write_text("dirty\n")
            with self.assertRaisesRegex(PiSyncError, "dirty"):
                PiSyncTransaction(runner=fixture.runner).apply(
                    fixture.request(), state_path=fixture.state
                )
            (fixture.checkout / "dirty.txt").unlink()

            envelope = json.loads(fixture.state.read_text(encoding="utf-8"))
            envelope["payload"]["receipt"]["actor"] = "mallory"
            envelope["integrity"] = _digest(envelope["payload"])
            fixture.state.write_text(json.dumps(envelope), encoding="utf-8")
            with self.assertRaisesRegex(PiSyncError, "completion receipt"):
                PiSyncTransaction(runner=fixture.runner).apply(
                    fixture.request(), state_path=fixture.state
                )
        finally:
            fixture.close()

    def test_only_durable_integrated_ticket_produces_a_sync_binding(self) -> None:
        head = "a" * 40
        base = {
            "tickets": {
                "PIS-01": {
                    "state": "integrated",
                    "disposition": "completed",
                    "delivery_lineage": {"head_sha": head},
                }
            }
        }
        self.assertEqual((head, "PIS-01"), integrated_pi_sync_binding(base, "PIS-01"))
        for state, disposition in (
            ("pr-open", "completed"),
            ("verified", "open"),
            ("failed", "completed"),
        ):
            document = json.loads(json.dumps(base))
            document["tickets"]["PIS-01"]["state"] = state
            document["tickets"]["PIS-01"]["disposition"] = disposition
            with self.subTest(state=state), self.assertRaisesRegex(PiSyncError, "durably integrated"):
                integrated_pi_sync_binding(document, "PIS-01")

    def test_existing_unmarked_checkout_is_never_reset(self) -> None:
        fixture = Fixture()
        try:
            fixture.checkout.mkdir(parents=True)
            git(fixture.checkout, "init", "-b", "main")
            git(fixture.checkout, "config", "user.name", "Other")
            git(fixture.checkout, "config", "user.email", "other@example.com")
            (fixture.checkout / "unrelated.txt").write_text("keep\n")
            git(fixture.checkout, "add", "unrelated.txt")
            git(fixture.checkout, "commit", "-m", "unrelated")
            original = git(fixture.checkout, "rev-parse", "HEAD")

            with self.assertRaisesRegex(PiSyncError, "ownership marker"):
                PiSyncTransaction(runner=fixture.runner).apply(
                    fixture.request(), state_path=fixture.state
                )

            self.assertEqual(original, git(fixture.checkout, "rev-parse", "HEAD"))
            self.assertEqual("keep\n", (fixture.checkout / "unrelated.txt").read_text())
        finally:
            fixture.close()

    def test_local_source_identity_resolves_only_against_settings_root(self) -> None:
        settings_root = Path("/tmp/pi-agent/config")
        checkout = Path("/tmp/pi-agent/local/agent-skills")
        self.assertTrue(
            _local_source_matches_checkout(
                "../local/agent-skills", checkout, settings_root
            )
        )
        self.assertTrue(
            _local_source_matches_checkout(
                checkout.as_posix(), checkout, settings_root
            )
        )
        self.assertFalse(
            _local_source_matches_checkout(
                "elsewhere/agent-skills", checkout, settings_root
            )
        )
        self.assertFalse(
            _local_source_matches_checkout(None, checkout, settings_root)
        )
        self.assertFalse(
            _local_source_matches_checkout("bad\0path", checkout, settings_root)
        )

    def test_pi_list_parser_counts_only_matching_package_rows(self) -> None:
        settings_root = Path("/tmp/pi-agent")
        checkout = settings_root / "local" / "agent-skills"
        output = (
            "User packages:\n"
            "  local/agent-skills (filtered)\n"
            f"    {checkout.as_posix()}\n"
            "  npm:other\n"
            "    /tmp/npm/other\n"
        )
        self.assertEqual(
            ["local/agent-skills", "npm:other"],
            _pi_list_package_sources(output),
        )
        self.assertEqual(
            1, _pi_list_checkout_count(output, checkout, settings_root)
        )
        installed_path_only = f"User packages:\n  npm:other\n    {checkout}\n"
        self.assertEqual(
            0,
            _pi_list_checkout_count(
                installed_path_only, checkout, settings_root
            ),
        )

    def test_settings_reconciliation_preserves_relative_source_and_rejects_duplicates(self) -> None:
        settings_root = Path("/tmp/pi-agent")
        checkout = settings_root / "local" / "agent-skills"
        document = {
            "other": {"unchanged": True},
            "packages": [
                "npm:a",
                {"source": GIT_SOURCE, "skills": []},
                "local/agent-skills",
                "npm:b",
            ],
        }
        result = _reconcile_settings(
            document,
            checkout,
            settings_root,
            replace_package_source=True,
        )
        self.assertEqual({"unchanged": True}, result["other"])
        self.assertEqual(
            [
                "npm:a",
                {"source": "local/agent-skills", "skills": []},
                "npm:b",
            ],
            result["packages"],
        )
        duplicate = dict(document)
        duplicate["packages"] = [*document["packages"], checkout.as_posix()]
        with self.assertRaisesRegex(PiSyncError, "exactly one local"):
            _reconcile_settings(
                duplicate,
                checkout,
                settings_root,
                replace_package_source=True,
            )
        mismatch = dict(document)
        mismatch["packages"] = [
            {"source": GIT_SOURCE, "skills": []},
            "local/not-agent-skills",
        ]
        with self.assertRaisesRegex(PiSyncError, "exactly one local"):
            _reconcile_settings(
                mismatch,
                checkout,
                settings_root,
                replace_package_source=True,
            )


if __name__ == "__main__":
    unittest.main()
