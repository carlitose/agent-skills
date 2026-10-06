from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import crew_messenger as cm


def toy_package(root: Path) -> Path:
    """A package holding every anchor once, as the installed 0.15.2 does."""
    files: dict[str, list[str]] = {}
    for rel, old, _new, count in cm.PATCHES:
        files.setdefault(rel, []).extend([old] * count)
    for rel, parts in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(parts) + "\nexport const keep = 1;\n", encoding="utf-8")
    (root / "package.json").write_text(json.dumps({"name": "pi-messenger", "version": "0.15.2"}), encoding="utf-8")
    return root


def installed_messenger() -> Path | None:
    try:
        import runner

        path = runner.installed_pi_config() / "node_modules" / "pi-messenger"
    except Exception:  # noqa: BLE001 - no installed Pi on this machine
        return None
    return path if path.is_dir() else None


class PrepareTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.source = toy_package(self.tmp / "src")
        self.dest = self.tmp / "out" / "pi-messenger"

    def assert_nothing_left(self):
        self.assertFalse(self.dest.exists())
        self.assertEqual([p.name for p in self.dest.parent.glob("*")] if self.dest.parent.exists() else [], [])

    def test_patches_every_anchor_and_writes_the_manifest(self):
        manifest = cm.prepare(self.source, self.dest)
        agents = (self.dest / "crew/agents.ts").read_text(encoding="utf-8")
        self.assertIn("spawn(process.execPath, [...dbenchWorkerArgv(), ...args], {", agents)
        self.assertIn(cm.WORKER_ARGS_KEPT, agents)
        self.assertIn("dbenchWorkerArgv }", (self.dest / "crew/lobby.ts").read_text(encoding="utf-8"))
        self.assertNotIn("feed.jsonl", (self.dest / "index.ts").read_text(encoding="utf-8"))
        self.assertIn(cm.HOME_WRAPPER, (self.dest / "config.ts").read_text(encoding="utf-8"))
        self.assertIn(cm.OS_HOME_WRAPPED, (self.dest / "crew/utils/discover.ts").read_text(encoding="utf-8"))
        on_disk = json.loads((self.dest / cm.MANIFEST).read_text(encoding="utf-8"))
        self.assertEqual(on_disk, manifest)
        self.assertEqual(manifest["version"], "0.15.2")
        self.assertEqual(len(manifest["patches"]), len(cm.PATCHES))
        self.assertIn("crew/agents.ts", manifest["source_sha256"])
        self.assertEqual(sorted(p.name for p in self.dest.parent.iterdir()), ["pi-messenger"])

    def test_a_missing_anchor_leaves_nothing(self):
        path = self.source / "crew/lobby.ts"
        path.write_text(path.read_text(encoding="utf-8").replace("spawn(getPiCommand()", "spawn(other()"), encoding="utf-8")
        with self.assertRaisesRegex(cm.PatchError, "crew/lobby.ts: anchor"):
            cm.prepare(self.source, self.dest)
        self.assert_nothing_left()

    def test_a_repeated_anchor_leaves_nothing(self):
        path = self.source / "crew/utils/config.ts"
        path.write_text(path.read_text(encoding="utf-8") + "os.homedir();\n", encoding="utf-8")
        with self.assertRaisesRegex(cm.PatchError, "occurs 2 times, expected 1"):
            cm.prepare(self.source, self.dest)
        self.assert_nothing_left()

    def test_a_new_home_lookup_fails_closed(self):
        (self.source / "crew/extra.ts").write_text('import { tmpdir, homedir } from "node:os";\n', encoding="utf-8")
        with self.assertRaisesRegex(cm.PatchError, "crew/extra.ts still reads the real home directory"):
            cm.prepare(self.source, self.dest)
        self.assert_nothing_left()

    def test_an_existing_destination_is_refused(self):
        self.dest.mkdir(parents=True)
        with self.assertRaisesRegex(cm.PatchError, "already exists"):
            cm.prepare(self.source, self.dest)

    def test_another_package_is_refused(self):
        (self.source / "package.json").write_text('{"name": "other"}', encoding="utf-8")
        with self.assertRaisesRegex(cm.PatchError, "is not pi-messenger"):
            cm.prepare(self.source, self.dest)

    @unittest.skipUnless(installed_messenger(), "pi-messenger is not installed here")
    def test_the_installed_package_patches_cleanly(self):
        cm.prepare(installed_messenger(), self.dest)
        for path in self.dest.rglob("*.ts"):
            text = path.read_text(encoding="utf-8")
            for leftover in cm.LEFTOVERS:
                self.assertNotIn(leftover, text, path)


def node_major() -> int:
    node = shutil.which("node")
    if not node:
        return 0
    out = subprocess.run([node, "--version"], capture_output=True, text=True, check=False).stdout
    return int(out.strip().lstrip("v").split(".")[0] or 0)


@unittest.skipUnless(node_major() >= 23, "needs Node with TypeScript type stripping")
class WorkerSpawnSmoke(unittest.TestCase):
    """The patched spawn line, run as TypeScript: no shell, so no EINVAL on Windows."""

    def test_spawns_node_with_the_benchmark_argv(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        child = tmp / "child.js"
        child.write_text("console.log(JSON.stringify(process.argv.slice(2)));\n", encoding="utf-8")
        script = tmp / "spawn.ts"
        script.write_text(
            'import { spawn } from "node:child_process";\n'
            + cm.ARGV_HELPER
            + 'const args = ["--mode", "json", "-p", "hello"];\n'
            + 'const proc = spawn(process.execPath, [...dbenchWorkerArgv(), ...args], {\n'
            + '  stdio: ["ignore", "inherit", "inherit"],\n});\n'
            + 'proc.on("error", (e) => { console.error("SPAWN", e.message); process.exit(3); });\n'
            + 'proc.on("exit", (code) => process.exit(code ?? 4));\n',
            encoding="utf-8",
        )
        env = {**os.environ, cm.ARGV_ENV: json.dumps([str(child), "--session-dir", str(tmp / "s")])}
        done = subprocess.run([shutil.which("node"), str(script)], capture_output=True, text=True, env=env, timeout=60, check=False)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout), ["--session-dir", str(tmp / "s"), "--mode", "json", "-p", "hello"])
        env.pop(cm.ARGV_ENV)
        missing = subprocess.run([shutil.which("node"), str(script)], capture_output=True, text=True, env=env, timeout=60, check=False)
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn(f"{cm.ARGV_ENV} is not set", missing.stderr)


if __name__ == "__main__":
    sys.exit(unittest.main())
