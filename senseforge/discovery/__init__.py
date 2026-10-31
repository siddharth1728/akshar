"""
SENSEFORGE M05: Discovery Forge Package
"""

from senseforge.discovery.candidate import PairedCandidate, EpistemicState, CandidateFitness
from senseforge.discovery.baselines import BaselineEvaluator, compute_nmse
from senseforge.discovery.pareto import (
    dominates,
    fast_non_dominated_sort,
    compute_crowding_distance,
    ParetoArchive,
)
from senseforge.discovery.forge import DiscoveryForge, ForgeConfig, GenerationSummary

