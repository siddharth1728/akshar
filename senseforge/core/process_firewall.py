"""
SENSEFORGE M02: Process-Separated Observation Firewall
Discovery-side client boundary providing genuine OS-level process isolation
against the World Process. Zero shared memory, zero pointer leakage.
"""

import sys
import subprocess
import json
import uuid
from typing import List, Optional, Tuple, Any

from senseforge.core.protocol import (
    PROTOCOL_VERSION,
    EnvSpawnRequest,
    EnvObserveRequest,
    EnvProbeRequest,
    EnvResetRequest,
    EnvPingRequest,
    EnvShutdownRequest,
    EnvFrameResponse,
    EnvStatusResponse,
    EnvErrorResponse,
    compute_canonical_frame_hash,
)
from senseforge.core.firewall import ObservationFrame, FirewallSecurityViolation, FirewallExecutionError


class ProcessBoundaryTerminatedError(FirewallExecutionError):
    """Raised when the isolated World Process terminates unexpectedly."""
    pass


class TamperDetectedError(FirewallSecurityViolation):
    """Raised when an observation frame fails cryptographic hash or sequence verification."""
    pass


class ProcessObservationFirewall:
    """
    Hardened, process-separated Observation Firewall client.
    The World Process runs in a separate OS process with its own memory space.
    Communication occurs exclusively via strict JSON-Lines over standard streams.
    """

    def __init__(
        self,
        family: str,
        seed: int,
        allowed_channels: List[int],
        step_size: float = 0.01,
        noise_std: float = 0.0,
        num_entities: int = 16,
        max_action_amplitude: float = 1.0,
        custom_params: Optional[dict] = None,
        env_id: Optional[str] = None
    ):
        self._env_id = env_id or f"sf_env_{uuid.uuid4().hex[:12]}"
        self._seq = 0
        self._allowed_channels = tuple(sorted(list(set(allowed_channels))))
        self._step_size = step_size
        self._last_frame_hash = "0" * 64
        self._step_count = 0
        self._sim_time = 0.0

        # Launch child process
        cmd = [sys.executable, "-m", "senseforge.core.world_process"]
        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Spawn environment in worker
        spawn_req = EnvSpawnRequest(
            seq=self._seq,
            env_id=self._env_id,
            family=family,
            seed=seed,
            allowed_channels=list(self._allowed_channels),
            step_size=step_size,
            noise_std=noise_std,
            num_entities=num_entities,
            max_action_amplitude=max_action_amplitude,
            custom_params=custom_params or {}
        )
        resp = self._send_request(spawn_req)
        if resp.get("type") != "STATUS" or resp.get("status") != "INITIALIZED":
            self.close()
            raise FirewallExecutionError(f"Failed to initialize world process: {resp}")
        self._seq += 1

    def _send_request(self, req_model) -> dict:
        if self._process.poll() is not None:
            stderr = self._process.stderr.read() if self._process.stderr else ""
            raise ProcessBoundaryTerminatedError(f"World Process has terminated (exit code {self._process.returncode}). Stderr: {stderr}")

        line = req_model.model_dump_json() + "\n"
        assert self._process.stdin is not None
        try:
            self._process.stdin.write(line)
            self._process.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            raise ProcessBoundaryTerminatedError(f"Failed writing to world process pipe: {e}") from None

        assert self._process.stdout is not None
        resp_line = self._process.stdout.readline()
        if not resp_line:
            raise ProcessBoundaryTerminatedError("World process closed pipe without returning response")

        try:
            resp_data = json.loads(resp_line)
        except Exception as e:
            raise FirewallExecutionError(f"Malformed response from world process: {e}") from None

        # Check for error response
        if resp_data.get("type") == "ERROR":
            err = EnvErrorResponse.model_validate(resp_data)
            raise FirewallExecutionError(f"World Process error [{err.error_code}]: {err.sanitized_message}")

        return resp_data

    def _process_frame_response(self, resp_data: dict) -> ObservationFrame:
        frame_resp = EnvFrameResponse.model_validate(resp_data)

        # Sequence and ID checks
        if frame_resp.seq != self._seq or frame_resp.env_id != self._env_id:
            raise TamperDetectedError(
                f"Protocol mismatch: expected seq={self._seq}, env_id={self._env_id}; "
                f"got seq={frame_resp.seq}, env_id={frame_resp.env_id}"
            )

        # Cryptographic chain verification
        if frame_resp.prev_frame_hash != self._last_frame_hash:
            raise TamperDetectedError(
                f"Hash chain broken: expected prev_hash={self._last_frame_hash}, "
                f"got {frame_resp.prev_frame_hash}"
            )

        expected_hash = compute_canonical_frame_hash(
            env_id=self._env_id,
            seq=self._seq,
            step_index=frame_resp.step_index,
            timestamp=frame_resp.timestamp,
            readings=frame_resp.readings,
            prev_frame_hash=frame_resp.prev_frame_hash,
        )

        if frame_resp.frame_hash != expected_hash:
            raise TamperDetectedError(
                f"Cryptographic frame hash verification failed! Computed {expected_hash}, received {frame_resp.frame_hash}"
            )

        self._last_frame_hash = frame_resp.frame_hash
        self._step_count = frame_resp.step_index
        self._sim_time = frame_resp.timestamp
        self._seq += 1

        return ObservationFrame(
            timestamp=frame_resp.timestamp,
            step_index=frame_resp.step_index,
            readings=tuple(frame_resp.readings),
            frame_hash=frame_resp.frame_hash,
        )

    def observe(self) -> ObservationFrame:
        """Query an observation frame over the process boundary."""
        req = EnvObserveRequest(seq=self._seq, env_id=self._env_id)
        resp = self._send_request(req)
        return self._process_frame_response(resp)

    def probe(self, action: Optional[List[float]] = None) -> ObservationFrame:
        """Apply a probe perturbation over the process boundary."""
        act = action if action is not None else []
        req = EnvProbeRequest(seq=self._seq, env_id=self._env_id, action=act)
        resp = self._send_request(req)
        return self._process_frame_response(resp)

    def reset(self, new_seed: Optional[int] = None) -> ObservationFrame:
        """Reset the environment in the isolated process."""
        self._last_frame_hash = "0" * 64
        req = EnvResetRequest(seq=self._seq, env_id=self._env_id, new_seed=new_seed)
        resp = self._send_request(req)
        return self._process_frame_response(resp)

    def ping(self) -> bool:
        """Ping the worker process."""
        req = EnvPingRequest(seq=self._seq, env_id=self._env_id)
        resp = self._send_request(req)
        self._seq += 1
        return resp.get("status") == "OK"

    def close(self):
        """Terminate the isolated world process."""
        if self._process.poll() is None:
            try:
                req = EnvShutdownRequest(seq=self._seq, env_id=self._env_id)
                self._send_request(req)
            except Exception:
                pass
            try:
                self._process.terminate()
                self._process.wait(timeout=1.0)
            except Exception:
                self._process.kill()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def allowed_channels(self) -> Tuple[int, ...]:
        return self._allowed_channels

    @property
    def num_observable_channels(self) -> int:
        return len(self._allowed_channels)

    @property
    def step_count(self) -> int:
        return self._step_count

    @property
    def sim_time(self) -> float:
        return self._sim_time

    @property
    def env_id(self) -> str:
        return self._env_id

    # Anti-leakage guards
    def __getattr__(self, name: str) -> Any:
        if "_env" in name or "state" in name or "positions" in name or "velocities" in name:
            raise FirewallSecurityViolation(f"Process boundary forbids attribute inspection: '{name}'")
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

