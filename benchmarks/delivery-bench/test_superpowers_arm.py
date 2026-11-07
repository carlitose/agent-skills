"""Offline Superpowers arm contract: fake package, fake Pi, fake judge; no provider."""
from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import profile_report
import runner
from test_runner import Fixture, e_args, fake_pi_config, isolate_skills


class SuperpowersArmTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="dbench-superpowers-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = fake_pi_config(self.root / "config")
        self.package = self.root / "superpowers"
        self.names = ["executing-plans", "test-driven-development", "using-superpowers"]
        for name in self.names:
            path = self.package / "skills" / name / "SKILL.md"
            path.parent.mkdir(parents=True)
            path.write_text(f"---\nname: {name}\ndescription: Offline fixture\n---\nDo work.\n")
        self.bootstrap = self.package / ".pi/extensions/superpowers.ts"
        self.bootstrap.parent.mkdir(parents=True)
        self.bootstrap.write_text("export default function () {}\n")
        (self.package / "package.json").write_text(json.dumps({
            "name": "superpowers", "version": "7.0.2", "pi": {
                "extensions": ["./.pi/extensions/superpowers.ts"], "skills": ["./skills"]}}))
        isolate_skills(self, self.root)
        patcher = mock.patch.object(runner, "docker_command", return_value=None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def fixture(self, arms=("pi-superpowers",), **kwargs):
        original = runner.init_lot
        with mock.patch.object(runner, "init_lot", side_effect=lambda *a, **kw: original(
                *a, **kw, superpowers_root=self.package)):
            return Fixture(self.root, arms=arms, pi_config_root=self.config,
                           model="openai-codex/gpt-6-luna", thinking="medium", **kwargs)

    def test_cli_passes_the_snapshot_to_both_entry_points(self):
        for action, function, flags, result in (
                ("preflight", "preflight", ["--lot-free"], {"ok": True}),
                ("init-lot", "init_lot", ["--lot", "unused", "--lot-id", "t1", "--authority", "a",
                                         "--scenario", "toy=p", "--repetitions", "1"],
                 {"lot": "t1", "cells": {}})):
            with self.subTest(action=action), mock.patch.object(runner, function, return_value=result) as call:
                with contextlib.redirect_stdout(io.StringIO()):
                    code = runner.main([action, *flags, "--arm", "pi-superpowers", "--superpowers-root",
                                        str(self.package), "--model", "openai-codex/gpt-6-luna",
                                        "--thinking", "medium"])
                self.assertEqual(code, 0)
                self.assertEqual(call.call_args.kwargs["superpowers_root"], self.package)

    def test_lot_requires_a_snapshot_before_starting_pi(self):
        with self.assertRaisesRegex(ValueError, "superpowers"):
            runner.preflight(["pi-superpowers"], pi_config_root=self.config)

    def test_unselected_arm_does_not_load_the_package(self):
        with self.assertRaisesRegex(ValueError, "pi-superpowers"):
            runner.preflight(["bare"], superpowers_root=self.package)

    def test_manifest_bootstrap_and_bootstrap_skill_are_required(self):
        for relative in ("package.json", ".pi/extensions/superpowers.ts", "skills/using-superpowers/SKILL.md"):
            with self.subTest(relative=relative):
                path = self.package / relative
                content = path.read_bytes()
                path.unlink()
                try:
                    with self.assertRaisesRegex(ValueError, "[Ss]uperpowers|superpowers"):
                        runner.preflight(["pi-superpowers"], pi_config_root=self.config,
                                         superpowers_root=self.package)
                finally:
                    path.write_bytes(content)

    def test_argv_loads_only_explicit_superpowers_skills_with_the_same_tools_and_goal(self):
        fx = self.fixture(arms=("pi-tools", "pi-superpowers"))
        fx.run("toy.pi-tools.r1", 1)
        record = fx.run("toy.pi-superpowers.r1", 2)
        tools, first, second = [call["argv"] for call in fx.calls()]
        self.assertEqual(e_args(first), [*e_args(tools), str(self.bootstrap.resolve())])
        self.assertIn("--no-skills", first)
        self.assertEqual(first[first.index("--skill") + 1], str((self.package / "skills").resolve()))
        self.assertNotIn(str((self.config / runner.MANDATORY_EXTENSION).resolve()), e_args(first))
        self.assertEqual(first[-3:], ["--", runner.PROMPT, "/goal " + runner.GOAL_CONDITION])
        self.assertEqual(second[-4:], ["--continue", "--", runner.NEXT_PROMPT,
                                      "/goal " + runner.NEXT_GOAL_CONDITION])
        self.assertEqual(first[first.index("--model") + 1], "gpt-6-luna")
        self.assertEqual(first[first.index("--thinking") + 1], "medium")
        package = runner.load_lot(fx.lot)["superpowers"]
        self.assertEqual(package["skills"], self.names)
        self.assertEqual(package["version"], "7.0.2")
        self.assertEqual(record["requests"][0]["attempts"][0]["superpowers"], package)
        env = runner.arm_environment({}, "pi-superpowers")
        self.assertEqual(env["SUPERPOWERS_DISABLE_TELEMETRY"], "1")

    def test_package_drift_blocks_the_lot_and_attempt_before_pi(self):
        fx = self.fixture()
        lot = runner.load_lot(fx.lot)
        for relative in ("package.json", ".pi/extensions/superpowers.ts", "skills/executing-plans/SKILL.md"):
            path = self.package / relative
            content = path.read_bytes()
            path.write_bytes(content + b"\nchanged\n")
            try:
                with self.assertRaisesRegex(ValueError, "[Ss]uperpowers|superpowers"):
                    runner.load_lot(fx.lot)
                with self.assertRaisesRegex(ValueError, "[Ss]uperpowers|superpowers"):
                    runner.arm_argv(lot, lot["cells"]["toy.pi-superpowers.r1"], 1)
            finally:
                path.write_bytes(content)
        self.assertFalse(fx.log.exists())

    def test_missing_binding_never_silently_runs_a_plain_tools_arm(self):
        fx = self.fixture()
        lot = runner.load_lot(fx.lot)
        lot.pop("superpowers")
        with self.assertRaisesRegex(ValueError, "[Ss]uperpowers|superpowers"):
            runner.arm_argv(lot, lot["cells"]["toy.pi-superpowers.r1"], 1)

    def observation(self, names):
        return {"tools": sorted({*runner.BUILTIN_TOOLS, "code", "todo", "plan_mode_complete",
                                 "web_search", "web_fetch"}), "skills": names,
                "routed": False, "code_write": "ok"}

    def test_preflight_requires_the_exact_package_skills_not_our_workflow(self):
        for names, routed, expected in ((self.names, False, []),
                (self.names + ["ask-skills"], False, ["unexpected"]),
                (self.names[:-1], False, ["missing"]), (self.names, True, ["mandatory"])):
            with self.subTest(names=names, routed=routed):
                observed = {**self.observation(names), "routed": routed}
                problems = runner.preflight_problems("pi-superpowers", observed, 0, None, 60,
                                                      superpowers_skills=self.names)
                if not expected:
                    self.assertEqual(problems, [])
                else:
                    self.assertIn(expected[0], " ".join(problems))

    def test_preflight_uses_the_same_binding_and_argv_without_a_real_provider(self):
        calls = []
        def capture(argv, *, cwd, **kwargs):
            calls.append(argv)
            (cwd / "preflight.txt").write_text("ok")
            session = Path(argv[argv.index("--session-dir") + 1])
            session.mkdir(parents=True)
            observed = self.observation(self.names)
            messages = [{"role": "system", "toolsAdded": observed["tools"], "sections": {
                "skills": "".join(f"<name>{name}</name>" for name in self.names)}},
                {"role": "user", "content": "preflight"},
                {"role": "toolResult", "toolName": "code", "isError": False},
                {"role": "assistant", "content": [], "stopReason": "stop"}]
            (session / "s.jsonl").write_text("\n".join(json.dumps({"type": "message", "message": m})
                                                               for m in messages))
            return b"", b"", 0
        with mock.patch.object(runner, "capture_command", side_effect=capture):
            report = runner.preflight(["pi-superpowers"], pi_config_root=self.config,
                superpowers_root=self.package, pi_command=["fake-pi"],
                model="openai-codex/gpt-6-luna", thinking="medium")
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["arms"]["pi-superpowers"]["superpowers"]["skills"], self.names)
        self.assertEqual(e_args(calls[0])[-1], str(self.bootstrap.resolve()))

    def test_report_and_arm_from_include_superpowers_against_contemporary_tools(self):
        fx = self.fixture(arms=("pi-tools", "pi-superpowers"))
        for arm in ("pi-tools", "pi-superpowers"):
            fx.run(f"toy.{arm}.r1", 3)
        profile, comparison, markdown = profile_report.report(fx.lot, base="pi-tools", through=3,
            arm_from={"pi-superpowers": fx.lot})
        self.assertEqual({row["arm"] for row in profile["totals"]}, {"pi-tools", "pi-superpowers"})
        self.assertEqual(comparison["versus"]["pi-superpowers"]["pairs"], 3)
        self.assertIsNone(comparison["winner"])  # one repetition cannot settle this tie
        self.assertIn("pi-superpowers", comparison["repeat_needed"])
        self.assertIn("pi-superpowers", markdown)
        # A second simulated repetition exercises the existing simpler-arm tie break.
        for arm in ("pi-tools", "pi-superpowers"):
            cell = json.loads((fx.lot / "cells" / f"toy.{arm}.r1" / "cell.json").read_text())
            cell["rep"] = 2
            runner.dump(fx.lot / "cells" / f"toy.{arm}.r2" / "cell.json", cell)
        _, settled, _ = profile_report.report(fx.lot, base="pi-tools", through=3)
        self.assertEqual(settled["winner"], "pi-tools")


if __name__ == "__main__":
    unittest.main()
