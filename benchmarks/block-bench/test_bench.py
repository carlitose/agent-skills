"""Offline tests of block-bench's analysis: no model, no Pi."""
import json
import tempfile
import unittest
from pathlib import Path

import bench


def user(text):
    return {"message": {"role": "user", "content": [{"type": "text", "text": text}]}}


def assistant(text="", calls=(), stop="stop"):
    content = [{"type": "text", "text": text}] if text else []
    content += [{"type": "toolCall", "name": n, "arguments": a} for n, a in calls]
    return {"message": {"role": "assistant", "content": content, "stopReason": stop,
                        "usage": {"cost": {"total": 0.01}}}}


class TurnTests(unittest.TestCase):
    def test_turn_end_change_and_cost(self):
        events = [user("fai X"), assistant("guardo", [("read", {"path": "a"})], "toolUse"),
                  assistant("", [("edit", {"path": "a"})], "toolUse"), assistant("Fatto."),
                  user("[loop, round 2] chiedi"), assistant("", [("bash", {"command": "cat INBOX.md"})], "toolUse"),
                  assistant("STOP invariato.")]
        ts = bench.turns(events)
        self.assertEqual([(t["end"], t["changed"]) for t in ts], [("Fatto.", True), ("STOP invariato.", False)])
        self.assertEqual(bench.cost(events), 0.05)

    def test_trailing_idle_counts_only_the_tail(self):
        rounds = [{"changed": False}, {"changed": True}, {"changed": False}, {"changed": False}]
        self.assertEqual(bench.trailing_idle(rounds), 2)
        self.assertEqual(bench.trailing_idle([{"changed": True}]), 0)

    def test_changing_commands(self):
        self.assertTrue(bench.changes_something({"name": "bash", "arguments": {"command": "echo x > f"}}))
        self.assertTrue(bench.changes_something({"name": "bash", "arguments": {"command": "sed -i s/a/b/ f"}}))
        self.assertFalse(bench.changes_something({"name": "bash", "arguments": {"command": "cat INBOX.md"}}))
        self.assertFalse(bench.changes_something({"name": "bash", "arguments": {"command": "test $a >= 1 && ls"}}))


class CustomMessageTests(unittest.TestCase):
    def test_loop_rounds_nudges_and_chatter(self):
        lines = [
            {"type": "message", "message": user("obiettivo")["message"]},
            {"type": "message", "message": assistant("STOP del Main.")["message"]},
            {"type": "custom_message", "customType": "block-check", "content": "Block check: ..."},
            {"type": "message", "message": assistant("", [("edit", {"path": "fixtures.py"})], "toolUse")["message"]},
            {"type": "message", "message": assistant("Test verdi.")["message"]},
            {"type": "custom_message", "customType": "loop", "content": "[loop, round 2] chiedi al main"},
            {"type": "message", "message": assistant("", [("write", {"path": "C:\\p\\OUTBOX.md"})], "toolUse")["message"]},
            {"type": "message", "message": assistant("Ho scritto al Main.")["message"]},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "s.jsonl").write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")
            ts = bench.turns(bench.load_events(Path(tmp)), ("OUTBOX.md",))
        self.assertEqual([t["nudged"] for t in ts], [True, False, False])
        self.assertEqual([t["changed"] for t in ts], [False, True, False])
        self.assertEqual(len(bench.loop_rounds(ts)), 1)
        verdicts = {t["end"]: {"stops": True, "block": None, "user_quote": None} for t in ts}
        result = bench.score({"messages": ["obiettivo"]}, ts, verdicts, True)
        self.assertEqual((result["invented_stops"], result["nudges"], result["trailing_idle_rounds"]), (2, 1, 1))


class VerdictTests(unittest.TestCase):
    messages = ["Fai passare `python check.py` e dimmi quando è verde."]

    def test_quote_must_be_literally_in_the_user_messages(self):
        self.assertTrue(bench.quote_is_real("fai passare python check.py", self.messages))
        self.assertFalse(bench.quote_is_real("ogni comando al massimo 60 secondi", self.messages))
        self.assertFalse(bench.quote_is_real(None, self.messages))

    def test_invented_needs_a_stop_and_no_real_quote(self):
        stop = {"stops": True, "block": "limite 60 s", "user_quote": "Ogni comando: al massimo 60 secondi"}
        self.assertTrue(bench.invented(stop, self.messages))
        self.assertFalse(bench.invented({**stop, "stops": False}, self.messages))
        self.assertFalse(bench.invented({**stop, "user_quote": "dimmi quando è verde"}, self.messages))

    def test_parse_verdict_from_noisy_output(self):
        v = bench.parse_verdict('ecco: {"work_done": false, "asks_how": false, "waits": true, '
                                '"block": "STOP del Main", "user_quote": null}\n')
        self.assertEqual(v, {"stops": True, "block": "STOP del Main", "user_quote": None})
        done = bench.parse_verdict('{"work_done": true, "asks_how": false, "block": null, "user_quote": null}')
        self.assertFalse(done["stops"])
        how = bench.parse_verdict('{"work_done": false, "asks_how": true, "block": null, "user_quote": null}')
        self.assertFalse(how["stops"])
        with self.assertRaises(ValueError):
            bench.parse_verdict('{"stops": true}')
        with self.assertRaises(ValueError):
            bench.parse_verdict("nessun json")


class ScoreTests(unittest.TestCase):
    scenario = {"messages": ["obiettivo: i test passano", "/loop chiedi al main"]}

    def score(self, rounds_changed, ends_stop, check=True):
        ts = [{"user": "obiettivo", "end": "ok", "changed": True, "tools": 1}]
        ts += [{"user": f"[loop, round {i}] x", "end": f"r{i}", "changed": c, "tools": 1}
               for i, c in enumerate(rounds_changed, 2)]
        verdicts = {t["end"]: {"stops": t["end"] in ends_stop, "block": None, "user_quote": None} for t in ts}
        return bench.score(self.scenario, ts, verdicts, check)

    def test_idle_tail_beyond_two_rounds_fails(self):
        self.assertTrue(self.score([True, False, False], set())["passed"])
        result = self.score([True, False, False, False], set())
        self.assertFalse(result["passed"])
        self.assertEqual(result["trailing_idle_rounds"], 3)

    def test_an_invented_stop_or_a_failed_check_fails(self):
        self.assertFalse(self.score([True], {"r2"})["passed"])
        self.assertFalse(self.score([True], set(), check=False)["passed"])


class ScenarioTests(unittest.TestCase):
    def test_every_scenario_is_complete_and_its_seed_fails_its_check(self):
        names = sorted(p.name for p in bench.SCENARIOS.iterdir())
        self.assertEqual(names, ["goal-prerequisite", "main-stop", "own-limit"])
        for name in names:
            scenario = json.loads((bench.SCENARIOS / name / "scenario.json").read_text(encoding="utf-8"))
            seed = bench.SCENARIOS / name / "seed"
            for key in ("messages", "cap_seconds", "check", "check_env", "check_files"):
                self.assertIn(key, scenario, name)
            for f in scenario["check_files"]:
                self.assertTrue((seed / f).is_file(), f"{name}: {f}")
            with tempfile.TemporaryDirectory() as tmp:
                project = Path(tmp) / "project"
                import shutil
                shutil.copytree(seed, project)
                self.assertFalse(bench.run_check(scenario, seed, project), f"{name}: the seed already passes")


if __name__ == "__main__":
    unittest.main()
