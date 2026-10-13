from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from typing import Mapping

import numpy as np

from .v79_hierarchical_biology import LatentBiology, generate_latent_biology


_SCHEMA = "UNIFIED_SYNTHETIC_INTEGRATION_MANIFEST_V1"
_SOURCE_COMMITS = {
    "stage81a3": "f5a8ebeddbcd52a94274a7f72ecda1f71b82d777",
    "v79_pr253": "1a0ab6e1108af924ca13e81caa3c70f3101d251c",
    "pr311": "2b6d3439105e087acdab53a318c57bbb468eae26",
    "pr315": "af03ef67d52651463944a6de3a08e101ad00e0ea",
}
_AUTHORITY_KEYS = (
    "target_selection_authorized",
    "representation_selection_authorized",
    "td60_authorized",
    "stage4_authorized",
    "training_authorized",
    "real_data_authorized",
    "synthetic_training_authorized",
)
_CANDIDATE = re.compile(r"(?:^|[^A-Z0-9])C[1-6](?:[^A-Z0-9]|$)", re.IGNORECASE)


@dataclass(frozen=True)
class IntegrationAuthority:
    source_commits: dict[str, str]
    authority: dict[str, bool]
    calibration: dict[str, str]


def _contains_candidate(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_candidate(k) or _contains_candidate(v) for k, v in value.items())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_candidate(v) for v in value)
    if isinstance(value, str):
        normalized = re.sub(r"[_-]+", " ", value)
        return _CANDIDATE.search(normalized) is not None
    return False


def validate_integration_manifest(manifest: Mapping[str, object]) -> IntegrationAuthority:
    if not isinstance(manifest, Mapping) or manifest.get("schema") != _SCHEMA:
        raise ValueError("integration manifest schema differs")
    sources = manifest.get("source_commits")
    if not isinstance(sources, Mapping) or dict(sources) != _SOURCE_COMMITS:
        raise ValueError("source identity drift detected")
    authority = manifest.get("authority")
    if not isinstance(authority, Mapping) or set(authority) != set(_AUTHORITY_KEYS):
        raise ValueError("authority field set differs")
    if any(authority[k] is not False for k in _AUTHORITY_KEYS):
        raise ValueError("integration authority escalation refused")
    calibration = manifest.get("calibration")
    if not isinstance(calibration, Mapping) or calibration.get("stat1_50k_physical_row_status") != "QUARANTINED_NOT_HARD_AUTHORITY":
        raise ValueError("50K STAT1 calibration caveat missing")
    return IntegrationAuthority(dict(sources), {k: False for k in _AUTHORITY_KEYS}, dict(calibration))


@dataclass(frozen=True)
class UnifiedBiologyConfig:
    n_cells: int = 480
    n_genes: int = 48
    n_donors: int = 16
    rare_fraction: float = 0.08
    rare_effect_scale: float = 1.25
    context_effect_scale: float = 0.25
    perturbation_fraction: float = 0.05
    extra_metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.n_cells < 1 or self.n_genes < 8 or self.n_donors < 2:
            raise ValueError("invalid unified biology dimensions")
        if not (0 < self.rare_fraction < 0.5):
            raise ValueError("rare_fraction must be between 0 and 0.5")
        if not (0 <= self.perturbation_fraction < 0.5):
            raise ValueError("perturbation_fraction must be between 0 and 0.5")
        if _contains_candidate(self.extra_metadata):
            raise ValueError("candidate identifiers are forbidden from generator configuration")


@dataclass(frozen=True)
class UnifiedBiologyWorld:
    broad_class: np.ndarray
    substate: np.ndarray
    donor_id: np.ndarray
    continuous_factors: np.ndarray
    expected_molecular_state: np.ndarray
    rare_eligible: np.ndarray
    rare_activity: np.ndarray
    context_state: np.ndarray
    perturbation_state: np.ndarray
    world_hash: str


def _biology_authority() -> dict[str, object]:
    return {
        "class_frequencies": [0.45, 0.35, 0.20],
        "substates_per_class": [2, 3, 2],
        "substate_prevalence": [1.0, 1.0, 1.0],
        "module_size_distribution": [6, 10, 14],
        "n_modules_per_substate": 2,
        "n_continuous_factors": 3,
        "substate_effect_scale": 0.8,
        "continuous_factor_scale": 0.06,
        "donor_effect_scale": 0.10,
        "baseline_log_mean": -0.2,
        "baseline_log_sd": 0.35,
    }


def _hash_arrays(arrays: Mapping[str, np.ndarray]) -> str:
    h = sha256()
    for name in sorted(arrays):
        a = np.ascontiguousarray(arrays[name])
        h.update(name.encode("utf-8"))
        h.update(str(a.dtype).encode("ascii"))
        h.update(json.dumps(a.shape).encode("ascii"))
        h.update(a.view(np.uint8))
    return h.hexdigest()


def _latent_with_expected(latent: LatentBiology, expected: np.ndarray) -> LatentBiology:
    expected = np.asarray(expected, dtype=np.float32)
    expected.setflags(write=False)
    hashes = dict(latent.truth_hashes)
    hashes["latent_abundance"] = sha256(np.ascontiguousarray(expected).view(np.uint8)).hexdigest()
    return LatentBiology(
        broad_class=latent.broad_class,
        substate=latent.substate,
        donor=latent.donor,
        continuous_factors=latent.continuous_factors,
        latent_abundance=expected,
        biological_total_scale=latent.biological_total_scale,
        truth_hashes=hashes,
    )


def build_unified_biology(config: UnifiedBiologyConfig, *, seed: int) -> UnifiedBiologyWorld:
    if _contains_candidate(config.extra_metadata):
        raise ValueError("candidate identifiers are forbidden from generator configuration")
    latent = generate_latent_biology(
        _biology_authority(), config.n_cells, config.n_genes, config.n_donors, int(seed)
    )
    rng = np.random.default_rng(int(seed) + 100_003)

    # Rare biology is an activity regime inside the same population. Eligibility is
    # biological (lineage/state) and donor recurrence is explicit; source is absent.
    rare_eligible = (latent.broad_class == 0) & (latent.substate == 1)
    donor_active = rng.binomial(1, 0.40, config.n_donors).astype(bool)
    donor_prevalence = np.where(donor_active, config.rare_fraction, 0.0)
    rare_activity = rare_eligible & (rng.random(config.n_cells) < donor_prevalence[latent.donor])
    if rare_eligible.any() and not rare_activity.any():
        ix = int(np.flatnonzero(rare_eligible)[0])
        rare_activity[ix] = True

    context_state = ((latent.broad_class == 1) & (latent.substate == 0)).astype(bool)
    perturbation_state = rng.random(config.n_cells) < config.perturbation_fraction

    expected = np.asarray(latent.latent_abundance, dtype=np.float64).copy()
    rare_genes = np.arange(min(6, config.n_genes))
    context_genes = np.arange(min(6, config.n_genes), min(12, config.n_genes))
    perturb_genes = np.arange(min(12, config.n_genes), min(18, config.n_genes))
    if len(rare_genes):
        expected[np.ix_(rare_activity, rare_genes)] *= np.exp(config.rare_effect_scale)
    if len(context_genes):
        expected[np.ix_(context_state, context_genes)] *= np.exp(config.context_effect_scale)
    if len(perturb_genes):
        expected[np.ix_(perturbation_state, perturb_genes)] *= np.exp(-0.35)
    expected = expected.astype(np.float32)

    arrays = {
        "broad_class": latent.broad_class.astype(np.int64),
        "substate": latent.substate.astype(np.int64),
        "donor_id": latent.donor.astype(np.int64),
        "continuous_factors": latent.continuous_factors.astype(np.float32),
        "expected_molecular_state": expected,
        "rare_eligible": rare_eligible.astype(bool),
        "rare_activity": rare_activity.astype(bool),
        "context_state": context_state.astype(bool),
        "perturbation_state": perturbation_state.astype(bool),
    }
    for arr in arrays.values():
        arr.setflags(write=False)
    world_hash = _hash_arrays(arrays)
    return UnifiedBiologyWorld(**arrays, world_hash=world_hash)


def world_as_latent_biology(world: UnifiedBiologyWorld) -> LatentBiology:
    """Internal observation adapter; candidate-free and controller-free."""
    base = LatentBiology(
        broad_class=world.broad_class,
        substate=world.substate,
        donor=world.donor_id,
        continuous_factors=world.continuous_factors,
        latent_abundance=world.expected_molecular_state,
        biological_total_scale=np.ones(len(world.donor_id), dtype=np.float32),
        truth_hashes={},
    )
    return _latent_with_expected(base, world.expected_molecular_state)
