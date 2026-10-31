"""
SENSEFORGE M06: Experimental Partitioning & Data Integrity Engine
Enforces strictly isolated seed partitions:
- EXPLORATION PARTITION (Evolutionary search and generation)
- VALIDATION PARTITION (Model selection, tuning, preliminary screening)
- LOCKED TEST PARTITION (Sealed confirmatory evaluation, untouched environments)
"""

from typing import List, Dict, Any, Optional
from enum import Enum
import hashlib
import json
from dataclasses import dataclass, field
import numpy as np


class PartitionType(str, Enum):
    EXPLORATION = "EXPLORATION"
    SEARCH = "EXPLORATION"  # Backward compatibility alias
    VALIDATION = "VALIDATION"
    LOCKED_TEST = "LOCKED_TEST"
    SEALED_CONFIRMATORY = "LOCKED_TEST"  # Backward compatibility alias


class PartitionSealedViolation(Exception):
    """Raised when an attempt is made to reuse, retune, or modify a candidate against a locked partition."""
    pass


@dataclass
class SeedPartition:
    partition_type: PartitionType
    seeds: List[int]
    is_locked: bool = False
    access_count: int = 0
    candidate_locks: Dict[str, str] = field(default_factory=dict)  # candidate_id -> config_hash

    def get_seeds(self, candidate_id: str, candidate_config_hash: str) -> List[int]:
        """
        Dispenses seeds with strict access control.
        If partition is LOCKED_TEST, a candidate can only access it with an immutable config hash.
        Any subsequent access with a modified config hash raises PartitionSealedViolation.
        """
        if self.partition_type == PartitionType.LOCKED_TEST:
            if candidate_id in self.candidate_locks:
                previous_hash = self.candidate_locks[candidate_id]
                if previous_hash != candidate_config_hash:
                    raise PartitionSealedViolation(
                        f"Candidate '{candidate_id}' attempted to access Locked Partition with modified "
                        f"configuration hash ({candidate_config_hash} != {previous_hash}). Retuning on locked test partition is strictly prohibited."
                    )
            self.candidate_locks[candidate_id] = candidate_config_hash
            self.is_locked = True

        self.access_count += 1
        return list(self.seeds)


class PartitionManager:
    """Manages independent, non-overlapping seed partitions for scientific integrity."""

    def __init__(
        self,
        exploration_seeds: Optional[List[int]] = None,
        validation_seeds: Optional[List[int]] = None,
        locked_test_seeds: Optional[List[int]] = None,
    ):
        e_seeds = exploration_seeds or list(range(1000, 1025))     # 25 exploration seeds
        v_seeds = validation_seeds or list(range(2000, 2020))      # 20 validation seeds
        l_seeds = locked_test_seeds or list(range(9000, 9035))     # 35 locked test seeds (N >= 30)

        # Assert zero overlap between partitions
        set_e = set(e_seeds)
        set_v = set(v_seeds)
        set_l = set(l_seeds)
        assert set_e.isdisjoint(set_v), "Exploration and Validation seed partitions must be mutually disjoint!"
        assert set_e.isdisjoint(set_l), "Exploration and Locked Test seed partitions must be mutually disjoint!"
        assert set_v.isdisjoint(set_l), "Validation and Locked Test seed partitions must be mutually disjoint!"

        self.partitions = {
            PartitionType.EXPLORATION: SeedPartition(PartitionType.EXPLORATION, e_seeds),
            PartitionType.VALIDATION: SeedPartition(PartitionType.VALIDATION, v_seeds),
            PartitionType.LOCKED_TEST: SeedPartition(PartitionType.LOCKED_TEST, l_seeds),
        }

    def get_partition(self, p_type: PartitionType) -> SeedPartition:
        # Support aliases
        if p_type == "SEARCH":
            return self.partitions[PartitionType.EXPLORATION]
        elif p_type == "SEALED_CONFIRMATORY":
            return self.partitions[PartitionType.LOCKED_TEST]
        return self.partitions[p_type]

    @staticmethod
    def calculate_minimum_sample_size(effect_size: float = 0.6, alpha: float = 0.01, power: float = 0.80) -> int:
        """
        Calculates minimum sample size for a paired two-tailed test.
        For d=0.6, alpha=0.01, power=0.80, minimum N is ~32.
        """
        z_alpha = 2.576
        z_beta = 0.842
        n = ((z_alpha + z_beta) / max(0.1, effect_size)) ** 2
        return int(np.ceil(n))
