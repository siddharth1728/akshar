"""
SENSEFORGE M04: Probe Action Language
Typed, composable experimental action primitives for controlled physical interventions.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
import numpy as np


class ProbeAction(ABC):
    """Abstract base class for experimental action primitives."""

    @property
    @abstractmethod
    def duration(self) -> int:
        """Discrete time steps consumed by this action."""
        pass

    @property
    @abstractmethod
    def energy_cost(self) -> float:
        """Cumulative squared action magnitude: sum |u|^2."""
        pass

    @property
    @abstractmethod
    def max_magnitude(self) -> float:
        """Maximum absolute action magnitude."""
        pass

    @abstractmethod
    def unroll(self, total_channels: int) -> List[List[float]]:
        """
        Unrolls the high-level action into a sequence of discrete step vectors.
        Each step vector has dimension total_channels.
        """
        pass

    @abstractmethod
    def to_canonical_dict(self) -> Dict[str, Any]:
        """Canonical dictionary representation."""
        pass

    @abstractmethod
    def clone(self) -> "ProbeAction":
        """Deep clone of this action."""
        pass


class WaitAction(ProbeAction):
    """Zero-action relaxation step allowing the system to evolve freely."""

    def __init__(self, steps: int = 5):
        if steps < 1:
            raise ValueError(f"Wait steps must be >= 1, got {steps}")
        self._steps = int(steps)

    @property
    def duration(self) -> int:
        return self._steps

    @property
    def energy_cost(self) -> float:
        return 0.0

    @property
    def max_magnitude(self) -> float:
        return 0.0

    def unroll(self, total_channels: int) -> List[List[float]]:
        return [[0.0] * total_channels for _ in range(self._steps)]

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {"type": "Wait", "steps": self._steps}

    def clone(self) -> "WaitAction":
        return WaitAction(self._steps)


class ObserveAction(ProbeAction):
    """Explicit passive observation window."""

    def __init__(self, steps: int = 1):
        if steps < 1:
            raise ValueError(f"Observe steps must be >= 1, got {steps}")
        self._steps = int(steps)

    @property
    def duration(self) -> int:
        return self._steps

    @property
    def energy_cost(self) -> float:
        return 0.0

    @property
    def max_magnitude(self) -> float:
        return 0.0

    def unroll(self, total_channels: int) -> List[List[float]]:
        return [[0.0] * total_channels for _ in range(self._steps)]

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {"type": "Observe", "steps": self._steps}

    def clone(self) -> "ObserveAction":
        return ObserveAction(self._steps)


class PerturbAction(ProbeAction):
    """Applies a constant bounded perturbation on target action channel."""

    def __init__(self, channel: int, magnitude: float, duration: int = 1):
        if channel < 0:
            raise ValueError(f"Channel must be >= 0, got {channel}")
        if duration < 1:
            raise ValueError(f"Duration must be >= 1, got {duration}")
        self.channel = int(channel)
        self.magnitude = float(magnitude)
        self._duration = int(duration)

    @property
    def duration(self) -> int:
        return self._duration

    @property
    def energy_cost(self) -> float:
        return (self.magnitude ** 2) * self._duration

    @property
    def max_magnitude(self) -> float:
        return abs(self.magnitude)

    def unroll(self, total_channels: int) -> List[List[float]]:
        steps = []
        for _ in range(self._duration):
            vec = [0.0] * total_channels
            if self.channel < total_channels:
                vec[self.channel] = self.magnitude
            steps.append(vec)
        return steps

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "type": "Perturb",
            "channel": self.channel,
            "magnitude": round(self.magnitude, 6),
            "duration": self._duration,
        }

    def clone(self) -> "PerturbAction":
        return PerturbAction(self.channel, self.magnitude, self._duration)


class ReversePerturbAction(ProbeAction):
    """Applies an inverted perturbation to test directional symmetry/hysteresis."""

    def __init__(self, channel: int, magnitude: float, duration: int = 1):
        if channel < 0:
            raise ValueError(f"Channel must be >= 0, got {channel}")
        if duration < 1:
            raise ValueError(f"Duration must be >= 1, got {duration}")
        self.channel = int(channel)
        self.magnitude = float(magnitude)
        self._duration = int(duration)

    @property
    def duration(self) -> int:
        return self._duration

    @property
    def energy_cost(self) -> float:
        return (self.magnitude ** 2) * self._duration

    @property
    def max_magnitude(self) -> float:
        return abs(self.magnitude)

    def unroll(self, total_channels: int) -> List[List[float]]:
        steps = []
        for _ in range(self._duration):
            vec = [0.0] * total_channels
            if self.channel < total_channels:
                vec[self.channel] = -self.magnitude
            steps.append(vec)
        return steps

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "type": "ReversePerturb",
            "channel": self.channel,
            "magnitude": round(self.magnitude, 6),
            "duration": self._duration,
        }

    def clone(self) -> "ReversePerturbAction":
        return ReversePerturbAction(self.channel, self.magnitude, self._duration)


class RepeatAction(ProbeAction):
    """Repeats a sub-action sequence multiple times."""

    def __init__(self, action: ProbeAction, count: int = 2):
        if count < 1:
            raise ValueError(f"Repeat count must be >= 1, got {count}")
        self.action = action
        self.count = int(count)

    @property
    def duration(self) -> int:
        return self.action.duration * self.count

    @property
    def energy_cost(self) -> float:
        return self.action.energy_cost * self.count

    @property
    def max_magnitude(self) -> float:
        return self.action.max_magnitude

    def unroll(self, total_channels: int) -> List[List[float]]:
        sub_steps = self.action.unroll(total_channels)
        return sub_steps * self.count

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "type": "Repeat",
            "action": self.action.to_canonical_dict(),
            "count": self.count,
        }

    def clone(self) -> "RepeatAction":
        return RepeatAction(self.action.clone(), self.count)


def action_from_dict(d: Dict[str, Any]) -> ProbeAction:
    """Deserializes canonical dictionary into a ProbeAction object."""
    t = d["type"]
    if t == "Wait":
        return WaitAction(steps=d["steps"])
    elif t == "Observe":
        return ObserveAction(steps=d["steps"])
    elif t == "Perturb":
        return PerturbAction(channel=d["channel"], magnitude=d["magnitude"], duration=d["duration"])
    elif t == "ReversePerturb":
        return ReversePerturbAction(channel=d["channel"], magnitude=d["magnitude"], duration=d["duration"])
    elif t == "Repeat":
        sub = action_from_dict(d["action"])
        return RepeatAction(action=sub, count=d["count"])
    else:
        raise ValueError(f"Unknown ProbeAction type: {t}")

