"""
Adversarial Security and Boundary Tests for Process-Separated Firewall (M02)
Tests process isolation, serialization boundaries, malicious tampering,
invalid messages, replay attacks, and process crash recovery.
"""

import pytest
import gc
import pickle
import json
import numpy as np

from senseforge.core.environments.base import EnvironmentFamily
from senseforge.core.process_firewall import (
    ProcessObservationFirewall,
    TamperDetectedError,
    ProcessBoundaryTerminatedError,
)
from senseforge.core.firewall import FirewallSecurityViolation, FirewallExecutionError
from senseforge.core.protocol import EnvObserveRequest, EnvProbeRequest


def test_process_firewall_basic_lifecycle():
    """Verifies that the process firewall launches, queries, probes, and shuts down cleanly."""
    with ProcessObservationFirewall(
        family=EnvironmentFamily.COUPLED_OSCILLATORS,
        seed=12345,
        allowed_channels=[0, 2],
        num_entities=8
    ) as fw:
        assert fw.ping() is True
        assert fw.num_observable_channels == 2

        f0 = fw.observe()
        assert len(f0.readings) == 2
        assert f0.step_index == 0
        assert len(f0.frame_hash) == 64

        f1 = fw.probe([0.5, -0.5])
        assert f1.step_index == 1
        assert f1.frame_hash != f0.frame_hash

        # Re-observe
        f2 = fw.observe()
        assert f2.step_index == 1


def test_heap_isolation_no_simulation_objects_in_discovery_memory():
    """
    Heap inspection via gc.get_objects() in an isolated discovery process
    must NOT find any instance of CoupledOscillatorsEnvironment or private state arrays.
    """
    import subprocess
    import sys
    code = """
import gc
from senseforge.core.environments.base import EnvironmentFamily
from senseforge.core.process_firewall import ProcessObservationFirewall

with ProcessObservationFirewall(family=EnvironmentFamily.COUPLED_OSCILLATORS, seed=999, allowed_channels=[0, 1]) as fw:
    _ = fw.observe()
    live = [type(obj).__name__ for obj in gc.get_objects()]
    assert "CoupledOscillatorsEnvironment" not in live, "Leaked into heap!"
    assert "ReactionDiffusionEnvironment" not in live, "Leaked into heap!"
    assert "ThermodynamicSwarmEnvironment" not in live, "Leaked into heap!"
print("ISOLATED_OK")
"""
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert "ISOLATED_OK" in res.stdout


def test_rejection_of_unauthorized_extra_fields():
    """Extra fields in requests must be strictly forbidden by protocol models."""
    with pytest.raises(Exception):
        # extra="forbid" in Pydantic models
        EnvObserveRequest(
            seq=0,
            env_id="test_env",
            unauthorized_exploit_field="malicious_payload"
        )


def test_adversarial_action_nan_inf_rejection():
    """Sending NaN or Inf in actions must be caught and rejected with an execution error."""
    with ProcessObservationFirewall(
        family=EnvironmentFamily.COUPLED_OSCILLATORS,
        seed=42,
        allowed_channels=[0]
    ) as fw:
        with pytest.raises(FirewallExecutionError):
            fw.probe([float("nan"), 1.0])


def test_replay_attack_detection():
    """
    Attempting to replay an old message with a stale sequence number
    must trigger an error from the World Process.
    """
    with ProcessObservationFirewall(
        family=EnvironmentFamily.COUPLED_OSCILLATORS,
        seed=42,
        allowed_channels=[0]
    ) as fw:
        _ = fw.observe()
        # Send raw message with stale sequence number seq=0 instead of expected seq=2
        raw_stale_msg = json.dumps({
            "protocol_version": "senseforge.ipc.v1",
            "type": "OBSERVE",
            "seq": 0,
            "env_id": fw.env_id
        }) + "\n"
        fw._process.stdin.write(raw_stale_msg)
        fw._process.stdin.flush()
        resp_line = fw._process.stdout.readline()
        resp = json.loads(resp_line)
        assert resp["type"] == "ERROR"
        assert resp["error_code"] == "SEQUENCE_MISMATCH"


def test_process_crash_detection():
    """
    If the World Process is forcefully terminated (SIGKILL / taskkill),
    the firewall must detect the dead process and raise ProcessBoundaryTerminatedError.
    """
    fw = ProcessObservationFirewall(
        family=EnvironmentFamily.REACTION_DIFFUSION,
        seed=101,
        allowed_channels=[0]
    )
    _ = fw.observe()

    # Forcefully terminate the child process
    fw._process.kill()
    fw._process.wait()

    with pytest.raises(ProcessBoundaryTerminatedError):
        fw.observe()


def test_restart_after_crash():
    """A crashed process firewall can be closed and a new instance cleanly spawned."""
    fw1 = ProcessObservationFirewall(
        family=EnvironmentFamily.THERMODYNAMIC_SWARM,
        seed=777,
        allowed_channels=[0]
    )
    _ = fw1.observe()
    fw1._process.kill()
    fw1.close()

    # Spawn new instance cleanly
    with ProcessObservationFirewall(
        family=EnvironmentFamily.THERMODYNAMIC_SWARM,
        seed=777,
        allowed_channels=[0]
    ) as fw2:
        frame = fw2.observe()
        assert frame.step_index == 0
        assert fw2.ping() is True
