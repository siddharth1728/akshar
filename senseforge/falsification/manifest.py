"""
SENSEFORGE M06: Candidate Freeze & Experiment Manifest System
Provides immutable cryptographic freeze locks on candidate discoveries
and serializes audit-grade provenance manifests.
"""

from typing import Dict, Any, Optional
import hashlib
import json
import time

from senseforge.discovery.candidate import PairedCandidate, EpistemicState


class CandidateFrozenError(Exception):
    """Raised when attempting to mutate or modify a frozen candidate."""
    pass


class FrozenCandidate:
    """
    An immutable wrapper around a PairedCandidate prepared for Confirmatory & Transfer testing.
    Its configuration hash is cryptographically sealed.
    """

    def __init__(self, candidate: PairedCandidate):
        self._candidate = candidate.clone()
        self._candidate.candidate_id = candidate.candidate_id  # Preserve exact candidate_id
        # Compute immutable configuration hash
        canonical_str = json.dumps(self._candidate.to_canonical_dict(), sort_keys=True, separators=(',', ':'))
        self._config_hash = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
        self._freeze_timestamp = time.time()
        self._is_frozen = True

    @property
    def candidate(self) -> PairedCandidate:
        return self._candidate

    @property
    def config_hash(self) -> str:
        return self._config_hash

    @property
    def freeze_timestamp(self) -> float:
        return self._freeze_timestamp

    @property
    def candidate_id(self) -> str:
        return self._candidate.candidate_id

    def to_manifest(
        self,
        source_family: str,
        falsification_report: Optional[Dict[str, Any]] = None,
        transfer_report: Optional[Dict[str, Any]] = None,
        seeds_partition: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generates audit-grade scientific provenance manifest."""
        manifest_payload = {
            "senseforge_version": "0.3.0-alpha",
            "dsl_version": "senseforge.dsl.v1",
            "probe_version": "senseforge.probe.v1",
            "candidate_id": self.candidate_id,
            "freeze_timestamp": self._freeze_timestamp,
            "config_hash": self._config_hash,
            "source_family": source_family,
            "state": self._candidate.state.value,
            "instrument": self._candidate.instrument.to_canonical_dict(),
            "probe": self._candidate.probe.to_canonical_dict(),
            "seeds_partition": seeds_partition or {},
            "falsification_report": falsification_report or {},
            "transfer_report": transfer_report or {},
        }
        manifest_str = json.dumps(manifest_payload, sort_keys=True, separators=(',', ':'))
        manifest_payload["manifest_signature"] = hashlib.sha256(manifest_str.encode('utf-8')).hexdigest()
        return manifest_payload
