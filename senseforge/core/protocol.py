"""
SENSEFORGE M02: Process Isolation Communication Protocol
Strict, versioned JSON-Lines protocol for inter-process isolation between
the World Process (simulation) and Discovery Process (researcher).
"""

from typing import List, Optional, Tuple, Literal
import hashlib
import json
from pydantic import BaseModel, Field, ConfigDict


PROTOCOL_VERSION = "senseforge.ipc.v1"


class BaseMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    protocol_version: Literal["senseforge.ipc.v1"] = PROTOCOL_VERSION
    seq: int = Field(ge=0, description="Monotonically increasing sequence number")
    env_id: str = Field(min_length=1, max_length=64, description="Environment session ID")


# --- Requests (Discovery Process -> World Process) ---

class EnvSpawnRequest(BaseMessage):
    type: Literal["SPAWN"] = "SPAWN"
    family: str
    seed: int
    allowed_channels: List[int] = Field(min_length=1)
    step_size: float = Field(gt=0.0, le=1.0, default=0.01)
    noise_std: float = Field(ge=0.0, le=10.0, default=0.0)
    num_entities: int = Field(gt=0, le=256, default=16)
    max_action_amplitude: float = Field(gt=0.0, le=100.0, default=1.0)
    custom_params: dict = Field(default_factory=dict)


class EnvObserveRequest(BaseMessage):
    type: Literal["OBSERVE"] = "OBSERVE"


class EnvProbeRequest(BaseMessage):
    type: Literal["PROBE"] = "PROBE"
    action: List[float] = Field(max_length=64, description="Perturbation action vector")


class EnvResetRequest(BaseMessage):
    type: Literal["RESET"] = "RESET"
    new_seed: Optional[int] = None


class EnvPingRequest(BaseMessage):
    type: Literal["PING"] = "PING"


class EnvShutdownRequest(BaseMessage):
    type: Literal["SHUTDOWN"] = "SHUTDOWN"


# --- Responses (World Process -> Discovery Process) ---

class EnvFrameResponse(BaseMessage):
    type: Literal["FRAME"] = "FRAME"
    timestamp: float
    step_index: int
    readings: List[float]
    prev_frame_hash: str
    frame_hash: str


class EnvStatusResponse(BaseMessage):
    type: Literal["STATUS"] = "STATUS"
    status: Literal["OK", "INITIALIZED", "RESET", "SHUTTING_DOWN"]


class EnvErrorResponse(BaseMessage):
    type: Literal["ERROR"] = "ERROR"
    error_code: str
    sanitized_message: str


def compute_canonical_frame_hash(
    env_id: str,
    seq: int,
    step_index: int,
    timestamp: float,
    readings: List[float],
    prev_frame_hash: str
) -> str:
    """
    Computes canonical chained SHA-256 hash across observation frames
    to verify message integrity and detect tampering.
    """
    canonical_payload = {
        "env_id": env_id,
        "seq": seq,
        "step_index": step_index,
        "timestamp": f"{timestamp:.8e}",
        "readings": [f"{r:.8e}" for r in readings],
        "prev_frame_hash": prev_frame_hash,
    }
    encoded = json.dumps(canonical_payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()

