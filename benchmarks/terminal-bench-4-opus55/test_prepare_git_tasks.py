"""Synthetic packaging tests; no benchmark instructions or hidden verifier read."""
import hashlib
import tempfile
import tomllib
import unittest
from pathlib import Path

from prepare_git_tasks import prepare_task


class PrepareGitTasksTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.source, self.target = root / "source", root / "derived"
        self.source.mkdir()
        self.verifier = 'verifier@sha256:' + 'b' * 64
        self.original = 'agent@sha256:' + 'a' * 64
        text = (f'schema_version = "1.0"\n[task]\nname = "terminal-bench/dummy"\n'
                f'[verifier]\nenvironment_mode = "separate"\n'
                f'[verifier.environment]\ndocker_image = "{self.verifier}"\n'
                f'[environment]\ndocker_image = "{self.original}"\n')
        (self.source / "task.toml").write_text(text, encoding="utf-8")
        (self.source / "instruction.md").write_text("synthetic task\n", encoding="utf-8")
        (self.source / "tests").mkdir()
        (self.source / "tests" / "test.sh").write_text("synthetic verifier\n", encoding="utf-8")
        self.frozen = {
            "name": "dummy", "registry_ref": "terminal-bench/dummy@sha256:" + "c" * 64,
            "task_toml_sha256": hashlib.sha256((self.source / "task.toml").read_bytes()).hexdigest(),
            "instruction_sha256": hashlib.sha256((self.source / "instruction.md").read_bytes()).hexdigest(),
        }
        self.binding = {
            "task": "dummy", "base_agent_image_ref": self.original,
            "derived_agent_image_id": "sha256:" + "d" * 64,
            "original_verifier_image_ref": self.verifier,
        }

    def test_only_agent_image_changes_and_all_arm_inputs_share_one_task(self):
        receipt = prepare_task(self.source, self.target, self.frozen, self.binding)
        original = tomllib.loads((self.source / "task.toml").read_text(encoding="utf-8"))
        derived = tomllib.loads((self.target / "task.toml").read_text(encoding="utf-8"))
        self.assertEqual(derived["environment"]["docker_image"], self.binding["derived_agent_image_id"])
        self.assertEqual(derived["verifier"], original["verifier"])
        self.assertEqual((self.target / "instruction.md").read_bytes(),
                         (self.source / "instruction.md").read_bytes())
        self.assertEqual((self.target / "tests" / "test.sh").read_bytes(),
                         (self.source / "tests" / "test.sh").read_bytes())
        self.assertEqual(receipt["task"], "dummy")
        for arm in ("pi-bare", "skills-only", "ticket-driver-c1a", "ticket-driver-c3a"):
            with self.subTest(arm=arm):
                self.assertEqual(tomllib.loads((self.target / "task.toml").read_text(encoding="utf-8"))["environment"]["docker_image"],
                                 self.binding["derived_agent_image_id"])

    def test_stale_source_or_binding_is_rejected_before_copy(self):
        self.frozen["instruction_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            prepare_task(self.source, self.target, self.frozen, self.binding)
        self.assertFalse(self.target.exists())
        self.frozen["instruction_sha256"] = hashlib.sha256((self.source / "instruction.md").read_bytes()).hexdigest()
        self.binding["original_verifier_image_ref"] = "other-verifier"
        with self.assertRaises(ValueError):
            prepare_task(self.source, self.target, self.frozen, self.binding)
        self.assertFalse(self.target.exists())

    def test_existing_or_repository_destination_is_never_overwritten(self):
        self.target.mkdir()
        with self.assertRaises(ValueError):
            prepare_task(self.source, self.target, self.frozen, self.binding)
        with self.assertRaises(ValueError):
            prepare_task(self.source, Path(__file__).parent / "untracked-destination", self.frozen, self.binding)


if __name__ == "__main__":
    unittest.main()
