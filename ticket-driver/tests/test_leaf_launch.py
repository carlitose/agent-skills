"""Pi CLI argv and contained, no-model startup across Windows and POSIX."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ticket-autopilot" / "scripts"))
import leaf  # noqa: E402
from autopilot.command_capture import capture_command  # noqa: E402


class PiLaunchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tdw-pi-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.shim = self.root / "pi.CMD"
        self.shim.write_bytes(b"@echo off\r\n")
        self.node = self.root / "node.EXE"
        self.node.write_bytes(b"fake binary")
        self.package = self.root / "node_modules" / "@earendil-works" / "pi-coding-agent"
        self.package.mkdir(parents=True)
        self.cli = self.package / "dist" / "bundle" / "cli.js"
        self.cli.parent.mkdir(parents=True)
        self.cli.write_bytes(b"// no model\n")
        self.metadata = self.package / "package.json"
        self.set_metadata({"name": "@earendil-works/pi-coding-agent", "bin": {"pi": "dist/bundle/cli.js"}})
        self.policy = {"provider": "anthropic", "model": "sample", "thinking": "medium"}

    def set_metadata(self, value):
        self.metadata.write_text(json.dumps(value), encoding="utf-8")

    def which(self, command):
        return {"pi": str(self.shim), "node": str(self.node)}.get(command)

    def test_windows_npm_shim_becomes_native_node_and_preserves_literal_arguments(self):
        extension = self.root / "auth.ts"
        extension.write_bytes(b"// no model\n")
        with patch.object(leaf.shutil, "which", side_effect=self.which), \
             patch.dict(os.environ, {"TICKET_DRIVER_PI_EXTENSION": str(extension)}):
            resolved = leaf.pi_command(platform="nt")
            with patch.object(leaf, "pi_command", return_value=resolved):
                argv = leaf.leaf_argv(None, self.policy, self.root / "sessions", "literal -- prompt")
        self.assertEqual(argv, [str(self.node.resolve()), str(self.cli.resolve()), "-p", "--provider", "anthropic",
                                "--model", "sample", "--thinking", "medium", "--session-dir",
                                str(self.root / "sessions"), "-e", str(extension.resolve()), "--", "literal -- prompt"])
        self.assertNotIn(str(self.shim), argv)
        self.shim = self.root / "pi.BAT"
        self.shim.write_bytes(b"@echo off\r\n")
        with patch.object(leaf.shutil, "which", side_effect=self.which):
            self.assertEqual(leaf.pi_command(platform="nt"), resolved)

    def test_windows_rejects_missing_package_node_and_escaping_bin(self):
        with patch.object(leaf.shutil, "which", side_effect=self.which):
            cases = [
                ({"name": "different", "bin": {"pi": "dist/bundle/cli.js"}}, "package"),
                ({"name": "@earendil-works/pi-coding-agent", "bin": {"pi": "../outside.js"}}, "outside"),
                ({"name": "@earendil-works/pi-coding-agent", "bin": {"pi": str(self.root / "outside.js")}}, "outside"),
                ({"name": "@earendil-works/pi-coding-agent", "bin": {}}, "bin"),
            ]
            for metadata, detail in cases:
                with self.subTest(detail=detail):
                    self.set_metadata(metadata)
                    with self.assertRaisesRegex(ValueError, detail):
                        leaf.pi_command(platform="nt")
            self.set_metadata({"name": "@earendil-works/pi-coding-agent", "bin": {"pi": "dist/bundle/cli.js"}})
        with patch.object(leaf.shutil, "which", side_effect=lambda command: str(self.shim) if command == "pi" else None):
            with self.assertRaisesRegex(ValueError, "Node"):
                leaf.pi_command(platform="nt")
        self.metadata.unlink()
        with patch.object(leaf.shutil, "which", side_effect=self.which):
            with self.assertRaisesRegex(ValueError, "package"):
                leaf.pi_command(platform="nt")
        with patch.object(leaf.shutil, "which", return_value=None):
            with self.assertRaisesRegex(ValueError, "Pi is unavailable"):
                leaf.pi_command(platform="nt")

    def test_native_windows_posix_and_fake_leaf_preserve_existing_paths(self):
        native = self.root / "pi.EXE"
        native.write_bytes(b"fake binary")
        with patch.object(leaf.shutil, "which", return_value=str(native)):
            self.assertEqual(leaf.pi_command(platform="nt"), [str(native.resolve())])
        posix = self.root / "pi"
        posix.write_bytes(b"#!/usr/bin/env node\n")
        with patch.object(leaf.shutil, "which", return_value=str(posix)):
            self.assertEqual(leaf.pi_command(platform="posix"), [str(posix.resolve())])
        fake = self.root / "fake_leaf.py"
        fake.write_bytes(b"# fake\n")
        with patch.object(leaf.shutil, "which", side_effect=AssertionError("fake leaf must not resolve pi")):
            argv = leaf.leaf_argv(str(fake), self.policy, self.root / "sessions", "prompt")
        self.assertEqual(argv, [sys.executable, "-B", str(fake.resolve()), "--session-dir",
                                str(self.root / "sessions"), "--", "prompt"])

    @unittest.skipUnless(os.name == "nt" and shutil.which("pi") and shutil.which("node"), "requires installed Pi on Windows")
    def test_installed_pi_version_uses_contained_node_without_model(self):
        command = leaf.pi_command()
        self.assertEqual(Path(command[0]).suffix.lower(), ".exe")
        output, error, code = capture_command([*command, "--version"], cwd=self.root,
                                              timeout_seconds=30, max_output_bytes=8192)
        self.assertEqual(code, 0, error)
        self.assertTrue(output.strip())
        self.assertEqual(list(self.root.rglob("*.jsonl")), [])


if __name__ == "__main__":
    unittest.main()
