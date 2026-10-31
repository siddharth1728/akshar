"""
SENSEFORGE M05: Paired Discovery Candidate Representation
Represents the co-evolved pair Ψ = (Φ, Π) where Φ is the measurement operator
and Π is the experimental intervention protocol.
"""

from typing import Tuple, List, Dict, Any, Optional
from enum import Enum
import uuid
from pydantic import BaseModel, Field

from senseforge.genome.candidate import InstrumentGenome
from senseforge.probes.genome import ProbeGenome


class EpistemicState(str, Enum):
    GENERATED = "GENERATED"
    UNDER_EVALUATION = "UNDER_EVALUATION"
    UNDER_FALSIFICATION = "UNDER_FALSIFICATION"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    PROVISIONAL_DISCOVERY = "PROVISIONAL_DISCOVERY"
    GENERALIZED_DISCOVERY = "GENERALIZED_DISCOVERY"


class CandidateFitness(BaseModel):
    """Multi-objective fitness vector for Pareto ranking."""
    info_gain: float = 0.0              # Delta I over passive baseline
    baseline_b_diff: float = 0.0        # Delta over conventional statistical features
    baseline_c_diff: float = 0.0        # Delta over random intervention baseline
    robustness: float = 0.0             # Consistency across independent held-out seeds
    simplicity: float = 0.0             # Negative complexity: -(ast_complexity + probe_duration)
    energy_efficiency: float = 0.0      # Negative energy: -probe_energy
    compute_efficiency: float = 0.0     # Negative compute: -ops_performed
    novelty: float = 0.0                # Behavioral distance from archive


class PairedCandidate:
    """
    The central discovery candidate Ψ = (Φ, Π).
    Pairs an evolvable measurement operator Φ with an experimental probe Π.
    """

    def __init__(
        self,
        instrument: InstrumentGenome,
        probe: ProbeGenome,
        candidate_id: Optional[str] = None,
        generation: int = 0,
        parent_candidate_ids: Optional[Tuple[str, ...]] = None,
        state: EpistemicState = EpistemicState.GENERATED,
    ):
        self.candidate_id = candidate_id or f"pair_{uuid.uuid4().hex[:12]}"
        self.instrument = instrument
        self.probe = probe
        self.generation = generation
        self.parent_candidate_ids = parent_candidate_ids or ()
        self.state = state
        self.fitness = CandidateFitness()
        self.evaluation_records: List[Dict[str, Any]] = []

        # Multi-objective bookkeeping
        self.pareto_rank: int = 0
        self.crowding_distance: float = 0.0

    @property
    def complexity(self) -> int:
        return self.instrument.complexity + self.probe.total_duration

    def clone(self) -> "PairedCandidate":
        """Clones candidate with new ID and parent linkage, preserving fitness and evaluation records."""
        cloned_inst = self.instrument.clone()
        cloned_probe = self.probe.clone()
        cand = PairedCandidate(
            instrument=cloned_inst,
            probe=cloned_probe,
            candidate_id=f"pair_{uuid.uuid4().hex[:12]}",
            generation=self.generation,
            parent_candidate_ids=(self.candidate_id,),
            state=self.state,
        )
        cand.fitness = self.fitness.model_copy()
        cand.evaluation_records = [dict(r) for r in self.evaluation_records]
        cand.pareto_rank = self.pareto_rank
        cand.crowding_distance = self.crowding_distance
        return cand

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Canonical dictionary representation for SQLite and JSON logging."""
        return {
            "candidate_id": self.candidate_id,
            "generation": self.generation,
            "state": self.state.value,
            "parent_candidate_ids": list(self.parent_candidate_ids),
            "fitness": self.fitness.model_dump(),
            "instrument": self.instrument.to_canonical_dict(),
            "probe": self.probe.to_canonical_dict(),
            "evaluation_count": len(self.evaluation_records),
        }

    @classmethod
    def from_canonical_dict(cls, d: Dict[str, Any]) -> "PairedCandidate":
        inst = InstrumentGenome.from_canonical_dict(d["instrument"])
        probe = ProbeGenome.from_canonical_dict(d["probe"])
        cand = cls(
            instrument=inst,
            probe=probe,
            candidate_id=d["candidate_id"],
            generation=d.get("generation", 0),
            parent_candidate_ids=tuple(d.get("parent_candidate_ids", ())),
            state=EpistemicState(d.get("state", EpistemicState.GENERATED.value)),
        )
        cand.fitness = CandidateFitness.model_validate(d.get("fitness", {}))
        return cand
