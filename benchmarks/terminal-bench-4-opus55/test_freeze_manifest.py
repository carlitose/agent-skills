"""No-network tests of the TBF-01 metadata freeze contract."""
import importlib.util
import json
import pathlib
import tempfile
import unittest

HERE = pathlib.Path(__file__).parent
SPEC = importlib.util.spec_from_file_location("freeze_manifest", HERE / "freeze_manifest.py")
freeze = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(freeze)


class FreezeManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = pathlib.Path(self.tmp.name)
        self.dataset = root / "tasks"
        self.registry = root / "registry.json"
        self.payload = {
            "package": "terminal-bench/terminal-bench", "type": "dataset",
            "content_hash": "sha256:" + "a" * 64, "id": "registry-version-id",
            "revision": 4, "tags": ["4.0.0"], "yanked_at": None, "tasks": [],
        }
        for index, name in enumerate(freeze.PILOT):
            task_dir = self.dataset / name
            task_dir.mkdir(parents=True)
            (task_dir / "task.toml").write_text(
                f'[task]\nname = "terminal-bench/{name}"\n[environment]\ngpus = 0\n',
                encoding="utf-8",
            )
            (task_dir / "instruction.md").write_text("task text", encoding="utf-8")
            self.payload["tasks"].append({
                "available": True,
                "task_version_id": str(index),
                "task_version": {"content_hash": f"{index + 1:064x}",
                                 "package": {"name": name, "org": {"name": "terminal-bench"}}},
            })
        self.save()

    def save(self):
        self.registry.write_text(json.dumps(self.payload), encoding="utf-8")

    def test_pinned_manifest_is_deterministic(self):
        first = freeze.build(self.registry, self.dataset)
        self.assertEqual(first, freeze.build(self.registry, self.dataset))
        self.assertEqual(first["dataset_task_count"], 3)
        self.assertEqual(first["dataset_ref"], "terminal-bench/terminal-bench@sha256:" + "a" * 64)
        self.assertEqual(first["gpu_exclusions"], [])
        self.assertEqual(first["pilot_tasks"], list(freeze.PILOT))

    def test_registry_drift_and_gpu_pilot_fail_closed(self):
        self.payload["tasks"][0]["available"] = False
        self.save()
        with self.assertRaisesRegex(ValueError, "unavailable"):
            freeze.build(self.registry, self.dataset)
        self.payload["tasks"][0]["available"] = True
        self.save()
        task_dir = self.dataset / freeze.PILOT[0]
        toml_file = task_dir / "task.toml"
        toml_file.write_text(toml_file.read_text(encoding="utf-8").replace("gpus = 0", "gpus = 1"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "pilot requires unavailable GPU"):
            freeze.build(self.registry, self.dataset)

    def test_unsafe_task_name_cannot_escape_download_root(self):
        self.payload["tasks"][0]["task_version"]["package"]["name"] = "../../elsewhere"
        self.save()
        with self.assertRaisesRegex(ValueError, "unsafe task name"):
            freeze.build(self.registry, self.dataset)

    def test_wrong_identity_and_missing_instruction_fail_closed(self):
        self.payload["package"] = "other/dataset"
        self.save()
        with self.assertRaisesRegex(ValueError, "wrong registry package"):
            freeze.build(self.registry, self.dataset)
        self.payload["package"] = "terminal-bench/terminal-bench"
        self.save()
        (self.dataset / freeze.PILOT[1] / "instruction.md").unlink()
        with self.assertRaisesRegex(ValueError, "missing downloaded task"):
            freeze.build(self.registry, self.dataset)


if __name__ == "__main__":
    unittest.main()
