from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping

import numpy as np

_ALLOWED = {
    "class_frequencies",
    "substates_per_class",
    "substate_prevalence",
    "module_size_distribution",
    "n_modules_per_substate",
    "n_continuous_factors",
    "substate_effect_scale",
    "continuous_factor_scale",
    "donor_effect_scale",
    "baseline_log_mean",
    "baseline_log_sd",
    "baseline_abundance_quantile_probs",
    "baseline_abundance_quantiles",
}
_OPTIONAL = {"baseline_abundance_quantile_probs", "baseline_abundance_quantiles"}
_CELL_BLOCK = 128


@dataclass(frozen=True)
class BiologyAuthority:
    class_frequencies: tuple[float, ...]
    substates_per_class: tuple[int, ...]
    substate_prevalence: tuple[float, ...]
    module_size_distribution: tuple[int, ...]
    n_modules_per_substate: int
    n_continuous_factors: int
    substate_effect_scale: float
    continuous_factor_scale: float
    donor_effect_scale: float
    baseline_log_mean: float
    baseline_log_sd: float
    baseline_abundance_quantile_probs: tuple[float, ...] | None = None
    baseline_abundance_quantiles: tuple[float, ...] | None = None


@dataclass(frozen=True)
class LatentBiology:
    broad_class: np.ndarray
    substate: np.ndarray
    donor: np.ndarray
    continuous_factors: np.ndarray
    latent_abundance: np.ndarray
    biological_total_scale: np.ndarray
    truth_hashes: dict[str, str]


def validate_biology_authority(authority: Mapping[str, Any]) -> BiologyAuthority:
    keys = set(authority)
    unknown = keys - _ALLOWED
    if unknown:
        raise ValueError(f"unknown or forbidden biology authority fields: {sorted(unknown)}")
    missing = (_ALLOWED - _OPTIONAL) - keys
    if missing:
        raise ValueError(f"missing biology authority fields: {sorted(missing)}")

    cf = tuple(float(x) for x in authority["class_frequencies"])
    spc = tuple(int(x) for x in authority["substates_per_class"])
    prev = tuple(float(x) for x in authority["substate_prevalence"])
    ms = tuple(int(x) for x in authority["module_size_distribution"])
    if len(cf) < 2 or len(spc) != len(cf):
        raise ValueError("class_frequencies and substates_per_class must align")
    if any(x <= 0 for x in cf) or not np.isclose(sum(cf), 1.0, atol=1e-6):
        raise ValueError("class_frequencies must be positive and sum to 1")
    if any(x < 1 for x in spc):
        raise ValueError("each class requires at least one substate")
    if len(prev) not in (1, len(cf)) or any(x <= 0 for x in prev):
        raise ValueError("substate_prevalence must be positive scalar-like or per-class")
    if not ms or any(x < 1 for x in ms):
        raise ValueError("module_size_distribution must contain positive sizes")

    for name in ("n_modules_per_substate", "n_continuous_factors"):
        if int(authority[name]) < 1:
            raise ValueError(f"{name} must be positive")
    for name in ("substate_effect_scale", "continuous_factor_scale", "donor_effect_scale", "baseline_log_sd"):
        if float(authority[name]) < 0:
            raise ValueError(f"{name} must be nonnegative")

    qprobs = authority.get("baseline_abundance_quantile_probs")
    qvals = authority.get("baseline_abundance_quantiles")
    if (qprobs is None) != (qvals is None):
        raise ValueError("baseline abundance quantile probabilities and values must be supplied together")
    qprobs_t = qvals_t = None
    if qprobs is not None:
        qprobs_t = tuple(float(x) for x in qprobs)
        qvals_t = tuple(float(x) for x in qvals)
        if len(qprobs_t) < 2 or len(qprobs_t) != len(qvals_t):
            raise ValueError("baseline abundance quantiles must align")
        if qprobs_t[0] != 0.0 or qprobs_t[-1] != 1.0 or any(b <= a for a, b in zip(qprobs_t, qprobs_t[1:])):
            raise ValueError("baseline abundance quantile probabilities must strictly increase from 0 to 1")
        if any(x <= 0 for x in qvals_t) or any(b < a for a, b in zip(qvals_t, qvals_t[1:])):
            raise ValueError("baseline abundance quantiles must be positive and nondecreasing")

    return BiologyAuthority(
        class_frequencies=cf,
        substates_per_class=spc,
        substate_prevalence=prev,
        module_size_distribution=ms,
        n_modules_per_substate=int(authority["n_modules_per_substate"]),
        n_continuous_factors=int(authority["n_continuous_factors"]),
        substate_effect_scale=float(authority["substate_effect_scale"]),
        continuous_factor_scale=float(authority["continuous_factor_scale"]),
        donor_effect_scale=float(authority["donor_effect_scale"]),
        baseline_log_mean=float(authority["baseline_log_mean"]),
        baseline_log_sd=float(authority["baseline_log_sd"]),
        baseline_abundance_quantile_probs=qprobs_t,
        baseline_abundance_quantiles=qvals_t,
    )


def _hash_array(x: np.ndarray) -> str:
    a = np.ascontiguousarray(x)
    return sha256(a.view(np.uint8)).hexdigest()


def generate_latent_biology(authority: Mapping[str, Any] | BiologyAuthority, n_cells: int,
                            n_genes: int, n_donors: int, seed: int) -> LatentBiology:
    """Generate the same frozen latent world while bounding peak dense memory.

    The original implementation accumulated a full float64 cell x gene log-abundance matrix and
    then allocated another full float64 abundance matrix before casting to float32.  At the frozen
    4,000 x 41,238 scale that creates multiple >1 GiB temporaries.  We preserve RNG draw order and
    float64 arithmetic, but materialize the final float32 abundance matrix in cell blocks.
    """
    a = authority if isinstance(authority, BiologyAuthority) else validate_biology_authority(authority)
    if n_cells < 1 or n_genes < 2 or n_donors < 1:
        raise ValueError("n_cells, n_genes, and n_donors must be positive")
    rng = np.random.default_rng(int(seed))

    broad_class = rng.choice(len(a.class_frequencies), size=n_cells, p=np.asarray(a.class_frequencies))
    substate = np.empty(n_cells, dtype=np.int64)
    for cls, n_states in enumerate(a.substates_per_class):
        ix = np.flatnonzero(broad_class == cls)
        if not len(ix):
            continue
        alpha = a.substate_prevalence[cls] if len(a.substate_prevalence) > 1 else a.substate_prevalence[0]
        probs = rng.dirichlet(np.full(n_states, alpha))
        substate[ix] = rng.choice(n_states, size=len(ix), p=probs)

    donor = np.tile(np.arange(n_donors, dtype=np.int64), int(np.ceil(n_cells / n_donors)))[:n_cells]
    rng.shuffle(donor)

    if a.baseline_abundance_quantiles is not None:
        q = (np.arange(n_genes, dtype=np.float64) + 0.5) / n_genes
        perm = rng.permutation(n_genes)
        baseline = np.interp(q, np.asarray(a.baseline_abundance_quantile_probs),
                             np.asarray(a.baseline_abundance_quantiles))
        baseline = baseline[perm]
        baseline = baseline / np.median(baseline)
        baseline_log = np.log(np.clip(baseline, 1e-12, None)) + a.baseline_log_mean
    else:
        baseline_log = rng.normal(a.baseline_log_mean, a.baseline_log_sd, size=n_genes)

    # Draw all anonymous substate modules in the original order, but retain one effect vector per
    # realized state instead of immediately broadcasting it into a full cell x gene matrix.
    state_effects: dict[tuple[int, int], np.ndarray] = {}
    for cls, n_states in enumerate(a.substates_per_class):
        for st in range(n_states):
            ix = np.flatnonzero((broad_class == cls) & (substate == st))
            if not len(ix):
                continue
            effect = np.zeros(n_genes, dtype=np.float64)
            for _ in range(a.n_modules_per_substate):
                m = int(rng.choice(a.module_size_distribution))
                m = min(max(1, m), n_genes)
                genes = rng.choice(n_genes, size=m, replace=False)
                sign = rng.choice(np.asarray([-1.0, 1.0]))
                effect[genes] += sign * a.substate_effect_scale
            state_effects[(cls, st)] = effect

    continuous_factors = rng.normal(size=(n_cells, a.n_continuous_factors))
    continuous_loadings = rng.normal(0.0, a.continuous_factor_scale,
                                     size=(a.n_continuous_factors, n_genes))
    donor_loadings = rng.normal(0.0, a.donor_effect_scale, size=(n_donors, n_genes))
    donor_total = rng.normal(0.0, a.donor_effect_scale, size=n_donors)
    cell_total_noise = rng.normal(0.0, a.continuous_factor_scale, size=n_cells)
    biological_total_scale = np.exp(donor_total[donor] + cell_total_noise)

    latent_abundance = np.empty((n_cells, n_genes), dtype=np.float32)
    for lo in range(0, n_cells, _CELL_BLOCK):
        hi = min(lo + _CELL_BLOCK, n_cells)
        block = np.broadcast_to(baseline_log, (hi - lo, n_genes)).copy()
        cls_block = broad_class[lo:hi]
        state_block = substate[lo:hi]
        for (cls, st), effect in state_effects.items():
            local = np.flatnonzero((cls_block == cls) & (state_block == st))
            if len(local):
                block[local] += effect
        block += continuous_factors[lo:hi] @ continuous_loadings
        block += donor_loadings[donor[lo:hi]]
        abundance = np.exp(np.clip(block, -20.0, 20.0))
        abundance *= biological_total_scale[lo:hi, None]
        latent_abundance[lo:hi] = abundance.astype(np.float32)

    arrays = {
        "broad_class": broad_class.astype(np.int64),
        "substate": substate.astype(np.int64),
        "donor": donor.astype(np.int64),
        "continuous_factors": continuous_factors.astype(np.float32),
        "latent_abundance": latent_abundance,
        "biological_total_scale": biological_total_scale.astype(np.float32),
    }
    for arr in arrays.values():
        arr.setflags(write=False)
    hashes = {name: _hash_array(arr) for name, arr in arrays.items()}
    return LatentBiology(**arrays, truth_hashes=hashes)
