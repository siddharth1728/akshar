"""
SENSEFORGE M04: Probe Genome
Representation of an active experimental intervention protocol.
"""

from typing import List, Tuple, Set, Dict, Any, Optional
import uuid
import copy
from senseforge.probes.actions import ProbeAction, action_from_dict


class ProbeGenome:
    """
    Experimental Probe Genome (Π).
    Contains a sequence of controlled experimental actions designed to disturb the system
    and expose latent dynamics.
    """

    def __init__(
        self,
        actions: List[ProbeAction],
        reproducibility_seed: int,
        genome_id: Optional[str] = None,
        generation_number: int = 0,
        parent_ids: Optional[Tuple[str, ...]] = None,
        mutation_history: Optional[List[str]] = None,
    ):
        if not actions:
            raise ValueError("ProbeGenome must contain at least one action primitive.")
        self.genome_id = genome_id or f"probe_{uuid.uuid4().hex[:12]}"
        self.actions = actions
        self.reproducibility_seed = reproducibility_seed
        self.generation_number = generation_number
        self.parent_ids = parent_ids or ()
        self.mutation_history = mutation_history or []

    @property
    def total_duration(self) -> int:
        """Total time steps consumed by the unrolled probe."""
        return sum(act.duration for act in self.actions)

    @property
    def total_energy(self) -> float:
        """Cumulative energetic cost sum(|u|^2)."""
        return sum(act.energy_cost for act in self.actions)

    @property
    def max_magnitude(self) -> float:
        """Peak intervention amplitude."""
        if not self.actions:
            return 0.0
        return max(act.max_magnitude for act in self.actions)

    @property
    def num_actions(self) -> int:
        return len(self.actions)

    @property
    def target_channels(self) -> Set[int]:
        channels = set()
        for act in self.actions:
            if hasattr(act, "channel"):
                channels.add(act.channel)
            elif hasattr(act, "action") and hasattr(act.action, "channel"):
                channels.add(act.action.channel)
        return channels

    def unroll(self, total_channels: int) -> List[List[float]]:
        """
        Unrolls high-level actions into a discrete step-by-step intervention schedule.
        """
        schedule: List[List[float]] = []
        for act in self.actions:
            schedule.extend(act.unroll(total_channels))
        return schedule

    def clone(self) -> "ProbeGenome":
        """Deep clone with new ID and parent linkage."""
        cloned_actions = [act.clone() for act in self.actions]
        return ProbeGenome(
            actions=cloned_actions,
            reproducibility_seed=self.reproducibility_seed,
            genome_id=f"probe_{uuid.uuid4().hex[:12]}",
            generation_number=self.generation_number,
            parent_ids=(self.genome_id,),
            mutation_history=list(self.mutation_history),
        )

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Canonical dictionary representation for SQLite and JSON logging."""
        return {
            "probe_version": "senseforge.probe.v1",
            "genome_id": self.genome_id,
            "total_duration": self.total_duration,
            "total_energy": round(self.total_energy, 6),
            "max_magnitude": round(self.max_magnitude, 6),
            "num_actions": self.num_actions,
            "target_channels": sorted(list(self.target_channels)),
            "reproducibility_seed": self.reproducibility_seed,
            "generation_number": self.generation_number,
            "parent_ids": list(self.parent_ids),
            "mutation_history": self.mutation_history,
            "actions": [act.to_canonical_dict() for act in self.actions],
        }

    @classmethod
    def from_canonical_dict(cls, d: Dict[str, Any]) -> "ProbeGenome":
        """Reconstructs a ProbeGenome from canonical dictionary."""
        actions = [action_from_dict(act_dict) for act_dict in d["actions"]]
        return cls(
            actions=actions,
            reproducibility_seed=d["reproducibility_seed"],
            genome_id=d["genome_id"],
            generation_number=d.get("generation_number", 0),
            parent_ids=tuple(d.get("parent_ids", ())),
            mutation_history=d.get("mutation_history", []),
        )

