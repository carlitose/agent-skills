from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ticket-autopilot" / "scripts"))

from autopilot.pi_command import SubprocessPiRunner
from autopilot.pi_sync import PiSyncError, PiSyncTransaction
from test_pi_sync import Fixture, git


# Standard npm cmd-shim output, retained as a boundary fixture (never executed).
NPM_SHIM = r'''@ECHO off
GOTO start
:find_dp0
SET dp0=%~dp0
EXIT /b
:start
SETLOCAL
CALL :find_dp0

IF EXIST "%dp0%\node.exe" (
  SET "_prog=%dp0%\node.exe"
) ELSE (
  SET "_prog=node"
  SET PATHEXT=%PATHEXT:;.JS;=;%
)

endLocal & goto #_undefined_# 2>NUL || title %COMSPEC% & "%_prog%"  "%dp0%\node_modules\@earendil-works\pi-coding-agent\dist\bundle\cli.js" %*
'''

CLI_FIXTURE = r'''
const fs = require("node:fs");
const path = require("node:path");
const root = process.env.PI_CODING_AGENT_DIR;
const settingsPath = path.join(root, "settings.json");
const logPath = path.join(root, "calls.json");
const calls = fs.existsSync(logPath) ? JSON.parse(fs.readFileSync(logPath, "utf8")) : [];
calls.push({argv: process.argv.slice(2), root, cwd: process.cwd()});
fs.writeFileSync(logPath, JSON.stringify(calls));
const settings = JSON.parse(fs.readFileSync(settingsPath, "utf8"));
if (process.argv[2] === "install") {
  settings.packages.push(process.argv[3]);
  fs.writeFileSync(settingsPath, JSON.stringify(settings));
  console.log("installed Ω");
} else if (process.argv[2] === "list") {
  console.log("User packages:");
  for (const entry of settings.packages) {
    const source = typeof entry === "string" ? entry : entry.source;
    console.log("  " + source);
    console.log("    " + path.resolve(root, source));
  }
} else {
  process.exit(3);
}
'''


def npm_fixture(root: Path) -> Path:
    prefix = root / "npm"
    package = prefix / "node_modules" / "@earendil-works" / "pi-coding-agent"
    entry = package / "dist" / "bundle" / "cli.js"
    entry.parent.mkdir(parents=True)
    entry.write_text(CLI_FIXTURE, encoding="utf-8")
    (package / "package.json").write_text(
        json.dumps({"name": "@earendil-works/pi-coding-agent", "bin": {"pi": "dist/bundle/cli.js"}}),
        encoding="utf-8",
    )
    (prefix / "pi.cmd").write_text(NPM_SHIM, encoding="utf-8")
    return prefix


@unittest.skipUnless(os.name == "nt" and shutil.which("node.exe"), "native Windows Node required")
class NativePiTransactionTests(unittest.TestCase):
    def test_sync_and_replay_preserve_literal_paths_without_zsh(self) -> None:
        fixture = Fixture()
        try:
            prefix = npm_fixture(fixture.root)
            fixture.checkout = fixture.root / "checkout %WPI_TOKEN%! & Ω"
            fixture.settings = fixture.settings.rename(fixture.settings.parent / "old-settings.json")
            settings_root = fixture.root / "config %WPI_TOKEN%! & Ω"
            settings_root.mkdir()
            fixture.settings = fixture.settings.rename(settings_root / "settings.json")
            before_external = (fixture.agents / "external" / "payload.txt").read_bytes()
            env = {
                "PATH": str(prefix) + os.pathsep + os.environ["PATH"],
                "PI_CODING_AGENT_DIR": "parent-config-must-not-change",
                "WPI_TOKEN": "must-not-expand",
            }
            with patch.dict(os.environ, env):
                transaction = PiSyncTransaction()
                result = transaction.apply(fixture.request(), state_path=fixture.state)
                replay = transaction.apply(fixture.request(), state_path=fixture.state)
                self.assertEqual(env["PI_CODING_AGENT_DIR"], os.environ["PI_CODING_AGENT_DIR"])
            self.assertEqual("completed", result["status"])
            self.assertTrue(replay["replayed"])
            self.assertTrue(result["reload_required"])
            calls = json.loads((settings_root / "calls.json").read_text(encoding="utf-8"))
            self.assertEqual([["install", fixture.checkout.as_posix()], ["list"], ["list"]], [c["argv"] for c in calls])
            self.assertTrue(all(Path(c["root"]) == settings_root for c in calls))
            self.assertTrue(all(Path(c["cwd"]) == fixture.checkout for c in calls))
            settings = json.loads(fixture.settings.read_text(encoding="utf-8"))
            self.assertEqual(["npm:other", {"source": fixture.checkout.as_posix(), "skills": []}], settings["packages"])
            self.assertEqual(before_external, (fixture.agents / "external" / "payload.txt").read_bytes())
        finally:
            fixture.close()


    def test_native_failures_restore_owned_state_without_a_receipt(self) -> None:
        cases = {
            "install-exit": 'process.exit(7);',
            "install-bytes": 'process.stdout.write(Buffer.from([255]));',
            "list-bytes": CLI_FIXTURE.replace('console.log("User packages:");', 'process.stdout.write(Buffer.from([255]));'),
            "list-stderr-bytes": CLI_FIXTURE.replace('console.log("User packages:");', 'process.stderr.write(Buffer.from([255])); console.log("User packages:");'),
            "bad-list": CLI_FIXTURE.replace('console.log("  " + source);', 'console.log("wrong row");'),
        }
        for name, cli in cases.items():
            with self.subTest(name=name):
                fixture = Fixture()
                try:
                    prefix = npm_fixture(fixture.root)
                    entry = prefix / "node_modules" / "@earendil-works" / "pi-coding-agent" / "dist" / "bundle" / "cli.js"
                    entry.write_text(cli, encoding="utf-8")
                    before = fixture.settings.read_bytes()
                    with patch.dict(os.environ, {"PATH": str(prefix) + os.pathsep + os.environ["PATH"]}):
                        reason = "could not be observed.*utf-8" if "bytes" in name else ".+"
                        with self.assertRaisesRegex(PiSyncError, reason):
                            PiSyncTransaction().apply(fixture.request(), state_path=fixture.state)
                    state = json.loads(fixture.state.read_text(encoding="utf-8"))["payload"]
                    self.assertIsNone(state["receipt"])
                    self.assertIsNotNone(state["error"])
                    self.assertEqual(before, fixture.settings.read_bytes())
                    self.assertEqual("old\n", (fixture.agents / "alpha" / "payload.txt").read_text())
                    self.assertEqual("keep\n", (fixture.agents / "external" / "payload.txt").read_text())
                    self.assertFalse((fixture.agents / ".agent-skills-install-manifest.json").exists())
                finally:
                    fixture.close()


@unittest.skipUnless(os.name == "nt" and shutil.which("pi") and shutil.which("node.exe"), "installed Windows npm Pi required")
class InstalledPiDisposableTests(unittest.TestCase):
    def test_installed_cli_syncs_only_disposable_configuration(self) -> None:
        fixture = Fixture()
        try:
            fixture.settings.write_text(
                json.dumps({"packages": [], "theme": "dark", "defaultProjectTrust": "never"}),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"PI_OFFLINE": "1", "PI_TELEMETRY": "0"}):
                request = fixture.request(replace=False)
                result = PiSyncTransaction().apply(request, state_path=fixture.state)
                replay = PiSyncTransaction().apply(request, state_path=fixture.state)
            self.assertEqual("completed", result["status"])
            self.assertTrue(replay["replayed"])
            self.assertTrue(result["reload_required"])
            settings = json.loads(fixture.settings.read_text(encoding="utf-8"))
            self.assertEqual("dark", settings["theme"])
            self.assertEqual(1, len(settings["packages"]))
            self.assertEqual([], settings["packages"][0]["skills"])
            self.assertEqual("keep\n", (fixture.agents / "external" / "payload.txt").read_text())
        finally:
            fixture.close()


class PiCommandContractTests(unittest.TestCase):
    def test_posix_retains_zsh_positional_arguments(self) -> None:
        for arguments, script in [
            (["list"], 'PI_CODING_AGENT_DIR="$1" pi list'),
            (["install", "checkout $value & Ω"], 'PI_CODING_AGENT_DIR="$1" pi install "$2"'),
        ]:
            with self.subTest(arguments=arguments), patch("autopilot.pi_command.sys.platform", "linux"), patch(
                "autopilot.pi_command.subprocess.run",
                return_value=subprocess.CompletedProcess([], 0, "output Ω".encode("utf-8"), b""),
            ) as process:
                result = SubprocessPiRunner().run(arguments, cwd=Path("checkout"), settings_root=Path("config & Ω"))
                self.assertEqual("output Ω", result.stdout)
                self.assertEqual(["zsh", "-lic", script, "agent-skills-pi-sync", "config & Ω", *arguments[1:]], process.call_args.args[0])
                self.assertIsNone(process.call_args.kwargs["env"])

    def test_windows_prefers_adjacent_node_and_does_not_mutate_parent_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            prefix = npm_fixture(root)
            adjacent = prefix / "node.exe"
            adjacent.write_bytes(b"boundary fixture")
            with patch("autopilot.pi_command.sys.platform", "win32"), patch(
                "autopilot.pi_command.shutil.which", return_value=str(prefix / "pi.cmd")
            ), patch("autopilot.pi_command.subprocess.run", return_value=subprocess.CompletedProcess([], 0, b"listed", b"")) as process:
                before = dict(os.environ)
                result = SubprocessPiRunner().run(["list"], cwd=root, settings_root=root / "config")
                self.assertEqual(before, dict(os.environ))
                self.assertEqual("listed", result.stdout)
                self.assertEqual(str(adjacent), process.call_args.args[0][0])
                self.assertEqual("list", process.call_args.args[0][-1])
                self.assertEqual(str(root / "config"), process.call_args.kwargs["env"]["PI_CODING_AGENT_DIR"])
                self.assertFalse(process.call_args.kwargs.get("text", False))
                self.assertFalse(process.call_args.kwargs.get("shell", False))

    def test_unsupported_or_contradictory_installations_never_launch(self) -> None:
        for case in ["missing-pi", "executable", "missing-node", "missing-entry", "identity", "entry-escape", "shim-mismatch", "malformed-json"]:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                prefix = npm_fixture(root)
                package = prefix / "node_modules" / "@earendil-works" / "pi-coding-agent"
                metadata_path = package / "package.json"
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                selected = str(prefix / "pi.cmd")
                node = root / "node.exe"
                node.write_bytes(b"boundary fixture")
                if case == "missing-pi":
                    selected = None
                elif case == "executable":
                    selected = str(node)
                elif case == "missing-entry":
                    (package / "dist" / "bundle" / "cli.js").unlink()
                elif case == "identity":
                    metadata["name"] = "other-package"
                elif case == "entry-escape":
                    metadata["bin"]["pi"] = str(node)
                elif case == "shim-mismatch":
                    (prefix / "pi.cmd").write_text("@echo off\nnode another-cli.js %*\n", encoding="utf-8")
                metadata_path.write_text("{" if case == "malformed-json" else json.dumps(metadata), encoding="utf-8")
                choices = {"pi": selected, "node.exe": None if case == "missing-node" else str(node)}
                with patch("autopilot.pi_command.sys.platform", "win32"), patch(
                    "autopilot.pi_command.shutil.which", side_effect=choices.get
                ), patch("autopilot.pi_command.subprocess.run") as process:
                    with self.assertRaises((ValueError, OSError)):
                        SubprocessPiRunner().run(["list"], cwd=root, settings_root=root / "config")
                    process.assert_not_called()

    def test_update_is_not_a_sync_operation(self) -> None:
        with patch("autopilot.pi_command.subprocess.run") as process:
            with self.assertRaisesRegex(ValueError, "only install"):
                SubprocessPiRunner().run(["update"], cwd=Path("."), settings_root=Path("."))
            process.assert_not_called()


class GitRepresentationTests(unittest.TestCase):
    def test_materialized_git_symlink_cannot_be_adopted_as_an_owned_file(self) -> None:
        fixture = Fixture()
        try:
            target = fixture.source / "link-target.txt"
            target.write_text("../../outside", encoding="utf-8")
            blob = git(fixture.source, "hash-object", "-w", str(target))
            target.unlink()
            git(fixture.source, "update-index", "--add", "--cacheinfo", f"120000,{blob},alpha/escape")
            git(fixture.source, "commit", "-m", "unsafe Git symlink")
            head = git(fixture.source, "rev-parse", "HEAD")
            tree = git(fixture.source, "rev-parse", "HEAD^{tree}")
            before = fixture.settings.read_bytes()
            count = int(os.environ.get("GIT_CONFIG_COUNT", "0"))
            with patch.dict(os.environ, {
                "GIT_CONFIG_COUNT": str(count + 1),
                f"GIT_CONFIG_KEY_{count}": "core.symlinks",
                f"GIT_CONFIG_VALUE_{count}": "false",
            }):
                with self.assertRaisesRegex(PiSyncError, "symlink or special file"):
                    PiSyncTransaction(runner=fixture.runner).apply(
                        fixture.request(head=head, tree=tree), state_path=fixture.state
                    )
            self.assertEqual(0, fixture.runner.install_calls)
            self.assertEqual(before, fixture.settings.read_bytes())
            self.assertEqual("old\n", (fixture.agents / "alpha" / "payload.txt").read_text())
        finally:
            fixture.close()


if __name__ == "__main__":
    unittest.main()
