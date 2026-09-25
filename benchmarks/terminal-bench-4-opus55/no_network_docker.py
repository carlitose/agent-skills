"""Local Docker provider that can enforce a *static* no-network policy.

Harbor's stock Docker provider enforces non-public policies only through its nftables
egress sidecar, which needs ``CONFIG_NFT_FIB_INET`` in the engine kernel. Docker
Desktop's kernel on the benchmark host lacks it, so Harbor correctly refuses to start a
task verifier that declares ``allow_internet = false``. When a policy is no-network from
start to finish, Docker's native ``network_mode: none`` enforces the same requirement
(the container has only loopback). Any policy that is public, an allowlist, or changes
after start keeps the stock behavior, including its fail-closed refusal. Tasks,
images, instructions and verifiers are unchanged.

Use with Harbor: ``--env no_network_docker:NoNetworkDockerEnvironment``.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from harbor.environments.capabilities import EnvironmentCapabilities
from harbor.environments.docker.docker import DockerEnvironment
from harbor.models.task.config import NetworkMode, TaskOS


class NoNetworkDockerEnvironment(DockerEnvironment):
    def __init__(self, *args, **kwargs):
        policy = kwargs.get("network_policy")
        phases = list(kwargs.get("phase_network_policies") or ())
        config = kwargs.get("task_env_config")
        # Set before the base constructor validates policy support against capabilities.
        self._static_no_network = (
            policy is not None and config is not None and config.os != TaskOS.WINDOWS
            and all(p.network_mode == NetworkMode.NO_NETWORK for p in [policy, *phases]))
        super().__init__(*args, **kwargs)

    @property
    def capabilities(self) -> EnvironmentCapabilities:
        stock = super().capabilities
        if not self._static_no_network or self._enable_egress_control:
            return stock
        return stock.model_copy(update={"disable_internet": True})

    def _write_egress_control_services_compose_file(self) -> Path | None:
        if not self._static_no_network or self._enable_egress_control:
            return super()._write_egress_control_services_compose_file()
        self._cleanup_egress_control_services_compose_file()
        services = {name: {"network_mode": "none"} for name in self._egress_controlled_service_names()}
        if not services:
            return None
        self._egress_control_services_compose_temp_dir = tempfile.TemporaryDirectory()
        path = Path(self._egress_control_services_compose_temp_dir.name) / "docker-compose-no-network.json"
        path.write_text(json.dumps({"services": services}, indent=2))
        self._egress_control_services_compose_path = path
        return path

    @property
    def _docker_compose_paths(self) -> list[Path]:
        paths = super()._docker_compose_paths
        if (self._static_no_network and not self._enable_egress_control
                and self._egress_control_services_compose_path):
            paths.append(self._egress_control_services_compose_path)
        return paths
