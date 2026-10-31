"""
SENSEFORGE M05: DISCOVERY FORGE
Coordinates the co-evolution of Measurement Operators (Φ) and Experimental Probes (Π)
under multi-objective Pareto optimization.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass, field

from senseforge.genome.types import DataType
from senseforge.genome.candidate import GenomeFactory, InstrumentGenome
from senseforge.probes.evolution import ProbeFactory, ProbeConstraints
from senseforge.probes.genome import ProbeGenome
from senseforge.discovery.candidate import PairedCandidate, EpistemicState, CandidateFitness
from senseforge.discovery.baselines import BaselineEvaluator
from senseforge.discovery.pareto import (
    fast_non_dominated_sort,
    compute_crowding_distance,
    ParetoArchive,
)


@dataclass
class ForgeConfig:
    population_size: int = 16
    max_generations: int = 10
    eval_seeds: List[int] = field(default_factory=lambda: [101, 202, 303])
    target_channel: int = 0
    forecast_horizon: int = 10
    pre_steps: int = 15
    p_mutate_inst: float = 0.6
    p_mutate_probe: float = 0.6
    p_crossover: float = 0.4
    p_simplify: float = 0.2
    archive_capacity: int = 30


@dataclass
class GenerationSummary:
    generation: int
    best_info_gain: float
    mean_info_gain: float
    best_diff_random: float
    archive_size: int
    provisional_discoveries: int
    rejected_count: int


class DiscoveryForge:
    """
    Autonomous discovery engine co-evolving Measurement Operators and Experimental Probes.
    """

    def __init__(
        self,
        firewall: Any,
        allowed_channels: List[int],
        config: Optional[ForgeConfig] = None,
        seed: int = 42
    ):
        self.firewall = firewall
        self.allowed_channels = allowed_channels
        self.config = config or ForgeConfig()
        self.rng = np.random.default_rng(seed)
        self.archive = ParetoArchive(max_capacity=self.config.archive_capacity)

        self.generation = 0
        self.population: List[PairedCandidate] = []
        self.history: List[GenerationSummary] = []
        self.rejected_archive: List[PairedCandidate] = []

        self._initialize_population(seed)

    def _initialize_population(self, seed: int):
        """Creates initial diverse population of paired candidates."""
        pop = []
        for i in range(self.config.population_size):
            cand_seed = seed + i * 17
            inst = GenomeFactory.create_random_genome(
                seed=cand_seed,
                allowed_channels=self.allowed_channels,
                target_type=DataType.SERIES,
                max_depth=4
            )
            probe = ProbeFactory.create_random_probe(
                seed=cand_seed + 1,
                allowed_action_channels=self.allowed_channels,
                num_actions=3
            )
            candidate = PairedCandidate(
                instrument=inst,
                probe=probe,
                generation=0,
                state=EpistemicState.GENERATED
            )
            pop.append(candidate)
        self.population = pop

    def evaluate_candidate(self, candidate: PairedCandidate) -> Dict[str, float]:
        """Evaluates candidate against all 4 baselines on held-out seeds."""
        candidate.state = EpistemicState.UNDER_EVALUATION
        results = BaselineEvaluator.evaluate_candidate_and_baselines(
            candidate=candidate,
            firewall=self.firewall,
            eval_seeds=self.config.eval_seeds,
            target_channel=self.config.target_channel,
            forecast_horizon=self.config.forecast_horizon,
            pre_steps=self.config.pre_steps
        )

        candidate.fitness = CandidateFitness(
            info_gain=results["info_gain"],
            baseline_b_diff=results["diff_b"],
            baseline_c_diff=results["diff_c"],
            robustness=results["robustness"],
            simplicity=-float(candidate.complexity),
            energy_efficiency=-float(candidate.probe.total_energy),
            compute_efficiency=-float(candidate.instrument.node_count),
            novelty=0.0
        )
        candidate.evaluation_records.append(results)

        # Epistemic classification
        if results["info_gain"] > 0.10 and results["diff_c"] > 0.05:
            candidate.state = EpistemicState.PROVISIONAL_DISCOVERY
        elif results["info_gain"] > 0.0:
            candidate.state = EpistemicState.INCONCLUSIVE
        else:
            candidate.state = EpistemicState.REJECTED

        return results

    def step(self) -> GenerationSummary:
        """Executes one generation of evaluation, Pareto selection, and reproduction."""
        # 1. Evaluate all candidates in population
        provisional_count = 0
        rejected_count = 0
        for cand in self.population:
            if not cand.evaluation_records:
                self.evaluate_candidate(cand)
            if cand.state == EpistemicState.PROVISIONAL_DISCOVERY:
                provisional_count += 1
            elif cand.state == EpistemicState.REJECTED:
                rejected_count += 1
                if len(self.rejected_archive) < 100:
                    self.rejected_archive.append(cand.clone())

        # 2. Update Pareto Archive with evaluated candidates
        self.archive.update(self.population)

        # 3. Compute generational summary stats
        info_gains = [c.fitness.info_gain for c in self.population]
        diff_randoms = [c.fitness.baseline_c_diff for c in self.population]
        summary = GenerationSummary(
            generation=self.generation,
            best_info_gain=float(np.max(info_gains)),
            mean_info_gain=float(np.mean(info_gains)),
            best_diff_random=float(np.max(diff_randoms)),
            archive_size=self.archive.size,
            provisional_discoveries=provisional_count,
            rejected_count=rejected_count,
        )
        self.history.append(summary)

        # 4. Multi-objective Pareto Ranking (NSGA-II)
        fronts = fast_non_dominated_sort(self.population)
        for front in fronts:
            compute_crowding_distance(front)

        # 5. Tournament Selection & Breeding Next Generation
        next_pop: List[PairedCandidate] = []

        # Elitism: retain top candidates from non-dominated front
        elite_count = min(2, len(fronts[0]))
        for i in range(elite_count):
            next_pop.append(fronts[0][i].clone())

        # Fill remaining population
        while len(next_pop) < self.config.population_size:
            p1 = self._tournament_select()
            p2 = self._tournament_select()

            off_inst = p1.instrument.clone()
            off_probe = p1.probe.clone()

            # Cross instruments?
            if self.rng.random() < self.config.p_crossover:
                off_inst, _ = GenomeFactory.crossover(p1.instrument, p2.instrument, self.rng)

            # Cross probes?
            if self.rng.random() < self.config.p_crossover:
                off_probe, _ = ProbeFactory.crossover(p1.probe, p2.probe, rng=self.rng)

            # Mutate instrument?
            if self.rng.random() < self.config.p_mutate_inst:
                m_type = self.rng.choice(["subtree", "operator", "constant"])
                if m_type == "subtree":
                    off_inst = GenomeFactory.mutate_subtree(off_inst, self.allowed_channels, max_depth=5, rng=self.rng)
                elif m_type == "operator":
                    off_inst = GenomeFactory.mutate_operator(off_inst, self.rng)
                else:
                    off_inst = GenomeFactory.mutate_constant(off_inst, self.rng)

            # Mutate probe?
            if self.rng.random() < self.config.p_mutate_probe:
                p_type = self.rng.choice(["magnitude", "timing", "sequence"])
                if p_type == "magnitude":
                    off_probe = ProbeFactory.mutate_magnitude(off_probe, rng=self.rng)
                elif p_type == "timing":
                    off_probe = ProbeFactory.mutate_timing(off_probe, rng=self.rng)
                else:
                    off_probe = ProbeFactory.mutate_sequence(off_probe, self.allowed_channels, rng=self.rng)

            # Simplify probe?
            if self.rng.random() < self.config.p_simplify:
                off_probe = ProbeFactory.simplify_probe(off_probe)

            child = PairedCandidate(
                instrument=off_inst,
                probe=off_probe,
                generation=self.generation + 1,
                parent_candidate_ids=(p1.candidate_id, p2.candidate_id),
                state=EpistemicState.GENERATED
            )
            next_pop.append(child)

        self.population = next_pop[:self.config.population_size]
        self.generation += 1
        return summary

    def _tournament_select(self, k: int = 2) -> PairedCandidate:
        """Binary tournament selection based on Pareto rank and crowding distance."""
        candidates = self.rng.choice(self.population, size=k, replace=False)
        best = candidates[0]
        for other in candidates[1:]:
            if other.pareto_rank < best.pareto_rank:
                best = other
            elif other.pareto_rank == best.pareto_rank and other.crowding_distance > best.crowding_distance:
                best = other
        return best

