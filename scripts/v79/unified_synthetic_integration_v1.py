from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from typing import Mapping

import numpy as np

from .v79_hierarchical_biology import LatentBiology, generate_latent_biology
from .v79_rare_biology_generator_v1 import REGIMES, RareWorldConfig, SIGNS, _donor_latent


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
    rare_regime_ids: tuple[str, ...] = ("weak", "central", "strong", "extreme")
    rare_effect_scale: float = 0.55
    context_niche_fraction: float = 0.35
    context_niche_multiplier: float = 8.0
    perturb_response_delta: float = 0.35
    extra_metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.n_cells < 1 or self.n_genes < 8 or self.n_donors < 2:
            raise ValueError("invalid unified biology dimensions")
        if not self.rare_regime_ids or any(r not in REGIMES for r in self.rare_regime_ids):
            raise ValueError("rare_regime_ids must use frozen PR311 regimes")
        if not (0 < self.context_niche_fraction < 1):
            raise ValueError("context_niche_fraction must lie in (0,1)")
        if self.context_niche_multiplier <= 0 or self.perturb_response_delta < 0:
            raise ValueError("context/perturbation parameters are invalid")
        if _contains_candidate(self.extra_metadata):
            raise ValueError("candidate identifiers are forbidden from generator configuration")


@dataclass(frozen=True)
class UnifiedBiologyWorld:
    broad_class: np.ndarray
    substate: np.ndarray
    donor_id: np.ndarray
    continuous_factors: np.ndarray
    expected_molecular_state: np.ndarray
    rare_regime_ids: tuple[str, ...]
    rare_eligible: np.ndarray
    rare_activity: np.ndarray
    rare_program_activity: np.ndarray
    rare_donor_active: np.ndarray
    rare_donor_prevalence: np.ndarray
    context_niche: np.ndarray
    perturbation_arm: np.ndarray
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


def _hash_arrays(arrays: Mapping[str, np.ndarray], *, labels: tuple[str, ...] = ()) -> str:
    h = sha256()
    for label in labels:
        h.update(label.encode("utf-8"))
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


def _program_eligibility(latent: LatentBiology, n_programs: int) -> np.ndarray:
    patterns = ((0, 1), (1, 0), (2, 0), (0, 0))
    out = np.zeros((len(latent.donor), n_programs), dtype=bool)
    for p in range(n_programs):
        cls, state = patterns[p % len(patterns)]
        out[:, p] = (latent.broad_class == cls) & (latent.substate == state)
    return out


def _context_niches(donor_id: np.ndarray, rng: np.random.Generator, fraction: float) -> np.ndarray:
    niche = np.zeros(len(donor_id), dtype=bool)
    for donor in np.unique(donor_id):
        ix = np.flatnonzero(donor_id == donor)
        n = len(ix)
        if n < 2:
            continue
        count = max(2, min(n, int(round(n * fraction))))
        start = int(rng.integers(0, n))
        local = (start + np.arange(count)) % n
        niche[ix[local]] = True
    return niche


def _balanced_perturbation_arms(donor_id: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    arms = np.zeros(len(donor_id), dtype=np.int8)
    for donor in np.unique(donor_id):
        ix = np.flatnonzero(donor_id == donor)
        local = np.tile(np.array([0, 1, 2], dtype=np.int8), int(np.ceil(len(ix) / 3)))[:len(ix)]
        rng.shuffle(local)
        arms[ix] = local
    return arms


def build_unified_biology(config: UnifiedBiologyConfig, *, seed: int) -> UnifiedBiologyWorld:
    if _contains_candidate(config.extra_metadata):
        raise ValueError("candidate identifiers are forbidden from generator configuration")
    latent = generate_latent_biology(
        _biology_authority(), config.n_cells, config.n_genes, config.n_donors, int(seed)
    )
    rng = np.random.default_rng(int(seed) + 100_003)
    regimes = tuple(config.rare_regime_ids)
    n_programs = len(regimes)
    eligibility = _program_eligibility(latent, n_programs)
    context_niche = _context_niches(latent.donor, rng, config.context_niche_fraction)

    donor_active = np.zeros((config.n_donors, n_programs), dtype=bool)
    donor_prevalence = np.zeros((config.n_donors, n_programs), dtype=np.float32)
    activity = np.zeros((config.n_cells, n_programs), dtype=bool)
    for p, regime in enumerate(regimes):
        prng = np.random.default_rng(int(seed) + 701 + 104729 * p)
        rare_cfg = RareWorldConfig(seed=int(seed), n_donors=config.n_donors, cells_per_donor=1, regime=regime, world="rna_only")
        active_p, prevalence_p = _donor_latent(prng, rare_cfg)
        donor_active[:, p] = active_p.astype(bool)
        donor_prevalence[:, p] = prevalence_p.astype(np.float32)
        for donor in range(config.n_donors):
            ix = np.flatnonzero((latent.donor == donor) & eligibility[:, p])
            if not len(ix) or prevalence_p[donor] <= 0:
                continue
            base_p = float(prevalence_p[donor])
            if p == 1:  # PR311 conditioned-context semantics embedded in this population.
                inside = context_niche[ix]
                n_in = int(inside.sum())
                p_in = min(0.5, base_p * config.context_niche_multiplier)
                expected = base_p * len(ix)
                remaining = max(0.0, expected - p_in * n_in)
                p_out = min(0.5, remaining / max(1, len(ix) - n_in))
                probs = np.where(inside, p_in, p_out)
            else:
                probs = np.full(len(ix), base_p, dtype=float)
            activity[ix, p] = prng.binomial(1, probs).astype(bool)

    rare_activity = activity.any(axis=1)
    rare_eligible = eligibility.any(axis=1)
    # At deterministic fixture scale, ensure every configured regime is represented
    # whenever it has eligible, active donors. This is not a prevalence calibration.
    for p in range(n_programs):
        if activity[:, p].any():
            continue
        candidates = np.flatnonzero(eligibility[:, p] & donor_active[latent.donor, p])
        if len(candidates):
            activity[int(candidates[0]), p] = True
    rare_activity = activity.any(axis=1)

    perturbation_arm = _balanced_perturbation_arms(latent.donor, rng)
    perturbation_state = (perturbation_arm == 1) & rare_activity

    expected = np.asarray(latent.latent_abundance, dtype=np.float64).copy()
    sign_template = np.asarray(SIGNS, dtype=float)
    block_width = min(len(sign_template), config.n_genes)
    for p in range(n_programs):
        genes = (np.arange(block_width) + p * block_width) % config.n_genes
        signs = sign_template[:block_width]
        cells = activity[:, p]
        if cells.any():
            multiplier = np.exp(config.rare_effect_scale * signs)
            expected[np.ix_(cells, genes)] *= multiplier[None, :]
    # PR311 perturbation actual/control/null semantics: only actual-arm rare cells
    # receive the additional response; null arm has no biological response.
    if perturbation_state.any():
        genes = np.arange(block_width) % config.n_genes
        response = np.exp(config.perturb_response_delta * sign_template[:block_width])
        expected[np.ix_(perturbation_state, genes)] *= response[None, :]
    expected = expected.astype(np.float32)

    arrays = {
        "broad_class": latent.broad_class.astype(np.int64),
        "substate": latent.substate.astype(np.int64),
        "donor_id": latent.donor.astype(np.int64),
        "continuous_factors": latent.continuous_factors.astype(np.float32),
        "expected_molecular_state": expected,
        "rare_eligible": rare_eligible.astype(bool),
        "rare_activity": rare_activity.astype(bool),
        "rare_program_activity": activity.astype(bool),
        "rare_donor_active": donor_active.astype(bool),
        "rare_donor_prevalence": donor_prevalence.astype(np.float32),
        "context_niche": context_niche.astype(bool),
        "perturbation_arm": perturbation_arm.astype(np.int8),
        "perturbation_state": perturbation_state.astype(bool),
    }
    for arr in arrays.values():
        arr.setflags(write=False)
    world_hash = _hash_arrays(arrays, labels=regimes)
    return UnifiedBiologyWorld(**arrays, rare_regime_ids=regimes, world_hash=world_hash)


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
