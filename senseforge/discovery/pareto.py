"""
SENSEFORGE M05: Multi-Objective Pareto Selection & Archive
Implements non-dominated sorting (NSGA-II) and a non-dominated archive
to maintain diverse, competing measurement-probe discoveries.
"""

from typing import List, Tuple, Dict, Any, Optional
import numpy as np

from senseforge.discovery.candidate import PairedCandidate, EpistemicState


def dominates(cand_a: PairedCandidate, cand_b: PairedCandidate) -> bool:
    """
    Candidate A dominates Candidate B (A ≻ B) if A is no worse than B in all objectives,
    and strictly better in at least one objective.
    Objectives to maximize:
    [info_gain, diff_c, robustness, simplicity, energy_efficiency]
    """
    fit_a = np.array([
        cand_a.fitness.info_gain,
        cand_a.fitness.baseline_c_diff,
        cand_a.fitness.robustness,
        cand_a.fitness.simplicity,
        cand_a.fitness.energy_efficiency,
    ])
    fit_b = np.array([
        cand_b.fitness.info_gain,
        cand_b.fitness.baseline_c_diff,
        cand_b.fitness.robustness,
        cand_b.fitness.simplicity,
        cand_b.fitness.energy_efficiency,
    ])

    at_least_as_good = np.all(fit_a >= fit_b - 1e-8)
    strictly_better = np.any(fit_a > fit_b + 1e-8)
    return bool(at_least_as_good and strictly_better)


def fast_non_dominated_sort(candidates: List[PairedCandidate]) -> List[List[PairedCandidate]]:
    """
    NSGA-II Fast Non-Dominated Sorting algorithm.
    Partitions candidates into Pareto fronts: F_0, F_1, F_2, ...
    """
    n = len(candidates)
    domination_counts = [0] * n        # n_p: number of solutions that dominate p
    dominated_solutions = [[] for _ in range(n)] # S_p: set of solutions that p dominates
    fronts: List[List[int]] = [[]]

    for p in range(n):
        for q in range(n):
            if p == q:
                continue
            if dominates(candidates[p], candidates[q]):
                dominated_solutions[p].append(q)
            elif dominates(candidates[q], candidates[p]):
                domination_counts[p] += 1

        if domination_counts[p] == 0:
            candidates[p].pareto_rank = 0
            fronts[0].append(p)

    i = 0
    while len(fronts[i]) > 0:
        next_front = []
        for p in fronts[i]:
            for q in dominated_solutions[p]:
                domination_counts[q] -= 1
                if domination_counts[q] == 0:
                    candidates[q].pareto_rank = i + 1
                    next_front.append(q)
        i += 1
        fronts.append(next_front)

    # Remove empty trailing front
    if fronts and not fronts[-1]:
        fronts.pop()

    return [[candidates[idx] for idx in front] for front in fronts]


def compute_crowding_distance(front: List[PairedCandidate]) -> None:
    """Computes crowding distance for candidates within a single Pareto front."""
    l = len(front)
    if l <= 2:
        for cand in front:
            cand.crowding_distance = float("inf")
        return

    for cand in front:
        cand.crowding_distance = 0.0

    # Objectives: info_gain, diff_c, robustness, simplicity, energy_efficiency
    objectives = [
        lambda c: c.fitness.info_gain,
        lambda c: c.fitness.baseline_c_diff,
        lambda c: c.fitness.robustness,
        lambda c: c.fitness.simplicity,
        lambda c: c.fitness.energy_efficiency,
    ]

    for obj in objectives:
        front.sort(key=obj)
        front[0].crowding_distance = float("inf")
        front[-1].crowding_distance = float("inf")

        val_min = obj(front[0])
        val_max = obj(front[-1])
        norm = max(1e-6, val_max - val_min)

        for i in range(1, l - 1):
            if front[i].crowding_distance != float("inf"):
                front[i].crowding_distance += (obj(front[i + 1]) - obj(front[i - 1])) / norm


class ParetoArchive:
    """Maintains a bounded non-dominated archive of scientific discoveries across generations."""

    def __init__(self, max_capacity: int = 50):
        self.max_capacity = max_capacity
        self.archive: List[PairedCandidate] = []

    def update(self, candidates: List[PairedCandidate]) -> int:
        """
        Updates the archive with new candidates, extracts the non-dominated set,
        and prunes if capacity is exceeded.
        Returns the number of new additions admitted to the archive.
        """
        combined = [c.clone() for c in self.archive] + [c.clone() for c in candidates if c.state != EpistemicState.REJECTED]
        if not combined:
            return 0

        fronts = fast_non_dominated_sort(combined)
        first_front = fronts[0] if fronts else []

        compute_crowding_distance(first_front)

        # If first front exceeds capacity, truncate based on crowding distance
        if len(first_front) > self.max_capacity:
            first_front.sort(key=lambda c: c.crowding_distance, reverse=True)
            self.archive = first_front[:self.max_capacity]
        else:
            self.archive = first_front

        return len(self.archive)

    @property
    def size(self) -> int:
        return len(self.archive)

    def get_best_by_metric(self, metric: str) -> Optional[PairedCandidate]:
        if not self.archive:
            return None
        return max(self.archive, key=lambda c: getattr(c.fitness, metric, -float("inf")))

