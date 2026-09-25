"""No Docker daemon: static no-network enforcement for the local Docker provider."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harbor.environments.docker.docker import DockerEnvironment
from harbor.models.task.config import EnvironmentConfig, NetworkMode, NetworkPolicy
from harbor.models.trial.paths import TrialPaths

from no_network_docker import NoNetworkDockerEnvironment

IMAGE = "registry/verifier@sha256:" + "b" * 64
NONE = NetworkPolicy(network_mode=NetworkMode.NO_NETWORK)
PUBLIC = NetworkPolicy(network_mode=NetworkMode.PUBLIC)


class NoNetworkDockerTests(unittest.TestCase):
    def setUp(self):
        probe = patch.object(DockerEnvironment, "_egress_control_kernel_support", return_value=False)
        probe.start()
        self.addCleanup(probe.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "environment").mkdir()

    def make(self, cls=NoNetworkDockerEnvironment, policy=NONE, phases=(NONE,)):
        return cls(environment_dir=self.root / "environment", environment_name="task",
                   session_id="session", trial_paths=TrialPaths(self.root / "trial"),
                   task_env_config=EnvironmentConfig(docker_image=IMAGE),
                   network_policy=policy, phase_network_policies=phases)

    def test_static_no_network_uses_docker_network_mode_none(self):
        env = self.make()
        self.assertTrue(env.capabilities.disable_internet)
        self.assertFalse(env.capabilities.dynamic_network_policy)
        path = env._write_egress_control_services_compose_file()
        self.assertEqual(json.loads(path.read_text()), {"services": {"main": {"network_mode": "none"}}})
        self.assertIn(path, env._docker_compose_paths)
        self.assertNotIn(env._DOCKER_COMPOSE_EGRESS_CONTROL_PATH, env._docker_compose_paths)
        env._cleanup_egress_control_services_compose_file()
        self.assertFalse(path.exists())

    def test_public_policy_is_byte_identical_to_the_stock_provider(self):
        ours, stock = self.make(policy=PUBLIC, phases=(PUBLIC,)), self.make(DockerEnvironment, PUBLIC, (PUBLIC,))
        self.assertEqual(ours.capabilities, stock.capabilities)
        self.assertIsNone(ours._write_egress_control_services_compose_file())
        self.assertEqual(ours._docker_compose_paths[:-1], stock._docker_compose_paths[:-1])
        self.assertEqual(len(ours._docker_compose_paths), len(stock._docker_compose_paths))

    def test_dynamic_or_allowlist_policies_still_fail_closed_like_the_stock_provider(self):
        allow = NetworkPolicy(network_mode=NetworkMode.ALLOWLIST, allowed_hosts=["example.com"])
        for policy, phases in ((PUBLIC, (NONE,)), (NONE, (PUBLIC,)), (allow, (allow,))):
            with self.assertRaises(ValueError, msg=str((policy, phases))):
                self.make(policy=policy, phases=phases)
            with self.assertRaises(ValueError):
                self.make(DockerEnvironment, policy, phases)

    def test_static_no_network_rejects_a_later_public_switch(self):
        env = self.make()
        import asyncio
        asyncio.run(env.set_network_policy(NONE))  # unchanged policy is a no-op
        with self.assertRaises(ValueError):
            asyncio.run(env.set_network_policy(PUBLIC))


if __name__ == "__main__":
    unittest.main()
