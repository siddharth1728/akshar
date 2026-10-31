"""
SENSEFORGE World Process Worker
Runs as an isolated process holding complete environment state.
Interacts with the outside discovery world strictly through standard input/output JSON-Lines.
Zero shared memory with the discovery engine.
"""

import sys
import json
import traceback
from typing import Optional, Dict
import numpy as np

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
from senseforge.core.environments.base import EnvironmentConfig, BaseEnvironment
from senseforge.core.environments import make_environment


class WorldProcessRunner:
    """
    Manages the environment lifecycle inside the isolated World Process.
    """

    def __init__(self):
        self._env: Optional[BaseEnvironment] = None
        self._env_id: Optional[str] = None
        self._allowed_channels: List[int] = []
        self._max_action_amplitude: float = 1.0
        self._expected_seq: int = 0
        self._prev_frame_hash: str = "0" * 64

    def _send_response(self, response_model):
        """Writes canonical JSON line to stdout and flushes."""
        raw = response_model.model_dump_json()
        sys.stdout.write(raw + "\n")
        sys.stdout.flush()

    def _send_error(self, seq: int, env_id: str, code: str, msg: str):
        err = EnvErrorResponse(
            seq=seq,
            env_id=env_id,
            error_code=code,
            sanitized_message=msg,
        )
        self._send_response(err)

    def _make_frame_response(self, seq: int) -> EnvFrameResponse:
        assert self._env is not None and self._env_id is not None
        raw_vec = self._env._get_raw_observable_vector()
        filtered = [float(raw_vec[ch]) for ch in self._allowed_channels]

        step_idx = int(self._env.step_count)
        ts = float(self._env.sim_time)
        current_hash = compute_canonical_frame_hash(
            env_id=self._env_id,
            seq=seq,
            step_index=step_idx,
            timestamp=ts,
            readings=filtered,
            prev_frame_hash=self._prev_frame_hash,
        )

        resp = EnvFrameResponse(
            seq=seq,
            env_id=self._env_id,
            timestamp=ts,
            step_index=step_idx,
            readings=filtered,
            prev_frame_hash=self._prev_frame_hash,
            frame_hash=current_hash,
        )
        self._prev_frame_hash = current_hash
        return resp

    def run(self):
        """Main event loop reading from stdin."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except Exception as e:
                self._send_error(0, "unknown", "MALFORMED_JSON", "Invalid JSON line received")
                continue

            # Validate basic envelope
            if not isinstance(data, dict):
                self._send_error(0, "unknown", "INVALID_MESSAGE", "Payload must be a JSON object")
                continue

            msg_type = data.get("type")
            req_seq = data.get("seq", -1)
            req_env_id = data.get("env_id", "unknown")

            # Sequence validation
            if req_seq != self._expected_seq:
                self._send_error(
                    req_seq,
                    req_env_id,
                    "SEQUENCE_MISMATCH",
                    f"Expected sequence number {self._expected_seq}, but received {req_seq}"
                )
                continue

            try:
                if msg_type == "SPAWN":
                    req = EnvSpawnRequest.model_validate(data)
                    config = EnvironmentConfig(
                        family=req.family,
                        seed=req.seed,
                        step_size=req.step_size,
                        noise_std=req.noise_std,
                        num_entities=req.num_entities,
                        custom_params=req.custom_params,
                    )
                    self._env = make_environment(config)
                    self._env_id = req.env_id
                    # Validate channels
                    total_ch = self._env.total_observable_channels
                    for ch in req.allowed_channels:
                        if ch < 0 or ch >= total_ch:
                            raise ValueError(f"Requested channel {ch} exceeds total channels {total_ch}")
                    self._allowed_channels = sorted(list(set(req.allowed_channels)))
                    self._max_action_amplitude = req.max_action_amplitude
                    self._prev_frame_hash = "0" * 64
                    self._expected_seq += 1

                    self._send_response(
                        EnvStatusResponse(
                            seq=req.seq,
                            env_id=req.env_id,
                            status="INITIALIZED",
                        )
                    )

                elif msg_type == "OBSERVE":
                    req = EnvObserveRequest.model_validate(data)
                    if self._env is None or self._env_id != req.env_id:
                        self._send_error(req.seq, req.env_id, "ENV_NOT_FOUND", "Environment not initialized or ID mismatch")
                        continue
                    self._expected_seq += 1
                    frame_resp = self._make_frame_response(req.seq)
                    self._send_response(frame_resp)

                elif msg_type == "PROBE":
                    req = EnvProbeRequest.model_validate(data)
                    if self._env is None or self._env_id != req.env_id:
                        self._send_error(req.seq, req.env_id, "ENV_NOT_FOUND", "Environment not initialized or ID mismatch")
                        continue

                    # Validate and clamp actions
                    raw_act = np.asarray(req.action, dtype=np.float64)
                    if np.isnan(raw_act).any() or np.isinf(raw_act).any():
                        self._send_error(req.seq, req.env_id, "INVALID_ACTION", "Action contains NaN or Inf values")
                        continue

                    clamped = np.clip(raw_act, -self._max_action_amplitude, self._max_action_amplitude)
                    self._env.step(clamped)
                    self._expected_seq += 1
                    frame_resp = self._make_frame_response(req.seq)
                    self._send_response(frame_resp)

                elif msg_type == "RESET":
                    req = EnvResetRequest.model_validate(data)
                    if self._env is None or self._env_id != req.env_id:
                        self._send_error(req.seq, req.env_id, "ENV_NOT_FOUND", "Environment not initialized or ID mismatch")
                        continue

                    self._env.reset(req.new_seed)
                    self._prev_frame_hash = "0" * 64
                    self._expected_seq += 1
                    frame_resp = self._make_frame_response(req.seq)
                    self._send_response(frame_resp)

                elif msg_type == "PING":
                    req = EnvPingRequest.model_validate(data)
                    self._expected_seq += 1
                    self._send_response(
                        EnvStatusResponse(seq=req.seq, env_id=req.env_id, status="OK")
                    )

                elif msg_type == "SHUTDOWN":
                    req = EnvShutdownRequest.model_validate(data)
                    self._send_response(
                        EnvStatusResponse(seq=req.seq, env_id=req.env_id, status="SHUTTING_DOWN")
                    )
                    break

                else:
                    self._send_error(req_seq, req_env_id, "UNKNOWN_COMMAND", f"Unsupported message type: {msg_type}")

            except Exception as e:
                # Sanitized error report: never expose stack traces or variable contents
                self._send_error(req_seq, req_env_id, "EXECUTION_ERROR", f"Sanitized simulator error: {type(e).__name__}")


if __name__ == "__main__":
    runner = WorldProcessRunner()
    runner.run()

