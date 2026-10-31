"""
SENSEFORGE M06: Falsification Chamber Package
"""

from senseforge.falsification.partition import (
    PartitionType,
    PartitionSealedViolation,
    SeedPartition,
    PartitionManager,
)
from senseforge.falsification.statistics import (
    StatisticalReport,
    StatisticalEngine,
)
from senseforge.falsification.chamber import (
    FalsificationChamber,
    compute_mse,
)
