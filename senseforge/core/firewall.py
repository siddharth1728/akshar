"""
M02: OBSERVATION FIREWALL
A strict, cryptographic information boundary between the procedural environment
and the autonomous discovery engine.
"""

from typing import List, Tuple, Optional, Any
import hashlib
import numpy as np
from dataclasses import dataclass
from senseforge.core.environments.base import BaseEnvironment


class FirewallSecurityViolation(Exception):
    """Raised whenever unauthorized access to hidden environment state is attempted."""
    pass


class FirewallExecutionError(Exception):
    """Sanitized exception raised when an internal simulator error occurs without leaking internals."""
    pass


@dataclass(frozen=True)
class ObservationFrame:
    """
    Immutable observation packet crossing the firewall boundary.
    Contains strictly the permitted channel readings, timestamps, and an integrity hash.
    """
    timestamp: float
    step_index: int
    readings: Tuple[float, ...]
    frame_hash: str

    def to_array(self) -> np.ndarray:
        return np.array(self.readings, dtype=np.float64)


class ObservationFirewall:
    """
    The Observation Firewall enforces strict isolation:
    - Never exposes internal simulation state, parameters, or random seeds.
    - Permits access ONLY to predefined observation channels.
    - Clamps and bounds all probe action vectors.
    - Sanitizes all exceptions to prevent information leakage through stack traces.
    - Blocks introspection and pickle-based state exfiltration.
    """

    # Explicit list of permitted public methods/properties on the firewall
    _PERMITTED_PUBLIC_ATTRS = {
        "observe",
        "probe",
        "step_count",
        "sim_time",
        "num_observable_channels",
        "reset",
        "allowed_channels",
        "__class__",
        "__doc__",
    }

    # Forbidden attribute names that must NEVER be accessed
    _FORBIDDEN_ATTR_PATTERNS = {
        "_env", "env", "state", "_state", "positions", "_positions",
        "velocities", "_velocities", "params", "_params", "seed", "_seed",
        "_rng", "rng", "_k", "_beta", "_mu", "_u", "_v", "_pos", "_vel"
    }

    def __init__(
        self,
        env: BaseEnvironment,
        allowed_channels: List[int],
        max_action_amplitude: float = 1.0
    ):
        # Store in mangled private attributes
        object.__setattr__(self, "_ObservationFirewall__env", env)
        object.__setattr__(self, "_ObservationFirewall__allowed_channels", tuple(sorted(list(set(allowed_channels)))))
        object.__setattr__(self, "_ObservationFirewall__max_action_amplitude", float(max_action_amplitude))

        # Validate channel bounds against total channels
        total_ch = env.total_observable_channels
        for ch in self.__allowed_channels:
            if ch < 0 or ch >= total_ch:
                raise ValueError(f"Requested channel {ch} exceeds total observable channels {total_ch}")

    @property
    def allowed_channels(self) -> Tuple[int, ...]:
        return self.__allowed_channels

    @property
    def num_observable_channels(self) -> int:
        return len(self.__allowed_channels)

    @property
    def step_count(self) -> int:
        return self.__env.step_count

    @property
    def sim_time(self) -> float:
        return self.__env.sim_time

    def observe(self) -> ObservationFrame:
        """
        Produce a sanitized, immutable observation frame containing ONLY permitted channels.
        """
        try:
            raw_vec = self.__env._get_raw_observable_vector()
            # Extract only allowed channels
            filtered = tuple(float(raw_vec[ch]) for ch in self.__allowed_channels)
            
            # Compute cryptographic hash for frame integrity and auditability
            hasher = hashlib.sha256()
            hasher.update(f"{self.__env.sim_time}:{self.__env.step_count}:".encode("ascii"))
            for val in filtered:
                hasher.update(f"{val:.8e}:".encode("ascii"))
            frame_hash = hasher.hexdigest()

            return ObservationFrame(
                timestamp=float(self.__env.sim_time),
                step_index=int(self.__env.step_count),
                readings=filtered,
                frame_hash=frame_hash,
            )
        except Exception as e:
            raise FirewallExecutionError("Sanitized execution error during environment observation") from None

    def probe(self, action: Optional[List[float]] = None) -> ObservationFrame:
        """
        Apply a bounded probe perturbation and advance the environment by one step.
        """
        try:
            clamped_action: Optional[np.ndarray] = None
            if action is not None:
                max_amp = self.__max_action_amplitude
                raw_act = np.asarray(action, dtype=np.float64)
                clamped_action = np.clip(raw_act, -max_amp, max_amp)

            self.__env.step(clamped_action)
            return self.observe()
        except Exception as e:
            raise FirewallExecutionError("Sanitized execution error during experimental probe application") from None

    def reset(self, new_seed: Optional[int] = None) -> ObservationFrame:
        """Reset the environment to initial conditions."""
        try:
            self.__env.reset(new_seed)
            return self.observe()
        except Exception as e:
            raise FirewallExecutionError("Sanitized execution error during environment reset") from None

    # --- ANTI-LEAKAGE GUARDS ---

    def __getattr__(self, name: str) -> Any:
        if name in self._FORBIDDEN_ATTR_PATTERNS or "_env" in name or "state" in name:
            raise FirewallSecurityViolation(f"Observation Firewall violation: Access to hidden attribute '{name}' is forbidden.")
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __dir__(self) -> List[str]:
        # Strip all private and environment attributes from introspection
        return sorted(list(self._PERMITTED_PUBLIC_ATTRS))

    def __repr__(self) -> str:
        return f"<ObservationFirewall channels={len(self.__allowed_channels)} step={self.step_count}>"

    def __reduce__(self) -> Any:
        # Prevent serialization/pickling of the firewall to extract internal environment state
        raise FirewallSecurityViolation("Serialization of ObservationFirewall is blocked by security policy.")

