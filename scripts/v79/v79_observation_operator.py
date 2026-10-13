from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping

import numpy as np
from scipy import sparse

from .v79_hierarchical_biology import LatentBiology

_ALLOWED = {
    "regime_ids", "structural_support", "structural_support_hex", "n_genes",
    "capture_log_mean", "capture_log_sd", "gene_propensity", "gene_propensity_constant",
    "realization_family", "molecule_scale",
}
_REQUIRED_BASE = {"regime_ids", "capture_log_mean", "capture_log_sd", "realization_family", "molecule_scale"}
_FAMILIES = {"independent_thinning", "conditional_multinomial"}


@dataclass(frozen=True)
class ObservationAuthority:
    regime_ids: tuple[str, ...]
    structural_support: tuple[tuple[bool, ...], ...]
    capture_log_mean: tuple[float, ...]
    capture_log_sd: tuple[float, ...]
    gene_propensity: tuple[float, ...]
    realization_family: str
    molecule_scale: float


@dataclass(frozen=True)
class ObservationResult:
    counts: sparse.csr_matrix
    structural_support: np.ndarray
    capture_efficiency: np.ndarray
    observed_library_totals: np.ndarray
    detected_counts: np.ndarray
    regime_labels: np.ndarray
    latent_truth_hash: str
    counts_hash: str


def validate_observation_authority(authority: Mapping[str, Any]) -> ObservationAuthority:
    keys = set(authority)
    unknown = keys - _ALLOWED
    if unknown:
        raise ValueError(f"unknown or forbidden observation authority fields: {sorted(unknown)}")
    missing = _REQUIRED_BASE - keys
    if missing:
        raise ValueError(f"missing observation authority fields: {sorted(missing)}")
    if ("structural_support" in keys) == ("structural_support_hex" in keys):
        raise ValueError("supply exactly one of structural_support or structural_support_hex")
    if "structural_support_hex" in keys and "n_genes" not in keys:
        raise ValueError("compact structural support requires n_genes")
    if ("gene_propensity" in keys) == ("gene_propensity_constant" in keys):
        raise ValueError("supply exactly one of gene_propensity or gene_propensity_constant")
    family = str(authority["realization_family"])
    if family not in _FAMILIES:
        raise ValueError(f"unrecognized realization family: {family}")
    regimes = tuple(str(x) for x in authority["regime_ids"])
    if "structural_support" in authority:
        support_arr = np.asarray(authority["structural_support"], dtype=bool)
    else:
        n_genes = int(authority["n_genes"])
        packed_rows = []
        for text in authority["structural_support_hex"]:
            raw = np.frombuffer(bytes.fromhex(str(text)), dtype=np.uint8)
            packed_rows.append(np.unpackbits(raw, bitorder="little")[:n_genes].astype(bool))
        support_arr = np.stack(packed_rows, axis=0) if packed_rows else np.empty((0, n_genes), dtype=bool)
    if support_arr.ndim != 2 or support_arr.shape[0] != len(regimes):
        raise ValueError("structural_support must be regime x gene")
    means = tuple(float(x) for x in authority["capture_log_mean"])
    sds = tuple(float(x) for x in authority["capture_log_sd"])
    if len(means) != len(regimes) or len(sds) != len(regimes):
        raise ValueError("capture parameters must align with regimes")
    if any(x < 0 for x in sds):
        raise ValueError("capture_log_sd must be nonnegative")
    if "gene_propensity" in authority:
        propensity = tuple(float(x) for x in authority["gene_propensity"])
    else:
        c = float(authority["gene_propensity_constant"])
        propensity = (c,) * int(support_arr.shape[1])
    if len(propensity) != support_arr.shape[1] or any(x <= 0 for x in propensity):
        raise ValueError("gene_propensity must be positive and match gene axis")
    scale = float(authority["molecule_scale"])
    if scale <= 0:
        raise ValueError("molecule_scale must be positive")
    return ObservationAuthority(
        regime_ids=regimes,
        structural_support=tuple(tuple(bool(v) for v in row) for row in support_arr),
        capture_log_mean=means,
        capture_log_sd=sds,
        gene_propensity=propensity,
        realization_family=family,
        molecule_scale=scale,
    )


def _latent_hash(latent: LatentBiology) -> str:
    h = sha256()
    for k in sorted(latent.truth_hashes):
        h.update(k.encode())
        h.update(latent.truth_hashes[k].encode())
    return h.hexdigest()


def _csr_hash(x: sparse.csr_matrix) -> str:
    x = x.tocsr()
    h = sha256()
    for arr in (x.indptr, x.indices, x.data):
        h.update(np.ascontiguousarray(arr).view(np.uint8))
    return h.hexdigest()


def observe_latent_biology(latent: LatentBiology, authority: Mapping[str, Any] | ObservationAuthority,
                           regime_labels: np.ndarray, seed: int) -> ObservationResult:
    a = authority if isinstance(authority, ObservationAuthority) else validate_observation_authority(authority)
    labels = np.asarray(regime_labels).astype(str)
    n_cells, n_genes = latent.latent_abundance.shape
    if labels.shape != (n_cells,):
        raise ValueError("regime_labels must have one entry per cell")
    if len(a.gene_propensity) != n_genes:
        raise ValueError("observation authority gene axis does not match latent biology")
    regime_to_ix = {r: i for i, r in enumerate(a.regime_ids)}
    if any(x not in regime_to_ix for x in labels):
        raise ValueError("unknown observation regime label")

    rng = np.random.default_rng(int(seed))
    support_table = np.asarray(a.structural_support, dtype=bool)
    support = np.vstack([support_table[regime_to_ix[x]] for x in labels])
    cap_mean = np.asarray([a.capture_log_mean[regime_to_ix[x]] for x in labels])
    cap_sd = np.asarray([a.capture_log_sd[regime_to_ix[x]] for x in labels])
    capture_efficiency = np.exp(rng.normal(cap_mean, cap_sd))
    propensity = np.asarray(a.gene_propensity, dtype=np.float64)

    base = latent.latent_abundance * propensity[None, :] * support
    if a.realization_family == "independent_thinning":
        rate = base * capture_efficiency[:, None] * a.molecule_scale
        dense = rng.poisson(np.clip(rate, 0.0, 1e8)).astype(np.int64)
    elif a.realization_family == "conditional_multinomial":
        dense = np.zeros((n_cells, n_genes), dtype=np.int64)
        biological_mass = np.asarray(latent.latent_abundance.sum(1)).ravel()
        expected_total = biological_mass * capture_efficiency * a.molecule_scale
        totals = rng.poisson(np.clip(expected_total, 0.0, 1e8))
        for i in range(n_cells):
            weights = base[i]
            s = float(weights.sum())
            if totals[i] > 0 and s > 0:
                dense[i] = rng.multinomial(int(totals[i]), weights / s)
    else:  # pragma: no cover - validator prevents this
        raise ValueError("unsupported realization family")

    counts = sparse.csr_matrix(dense)
    lib = np.asarray(counts.sum(1)).ravel().astype(np.int64)
    det = np.asarray((counts > 0).sum(1)).ravel().astype(np.int64)
    support.setflags(write=False)
    capture_efficiency.setflags(write=False)
    labels.setflags(write=False)
    lib.setflags(write=False)
    det.setflags(write=False)
    return ObservationResult(
        counts=counts,
        structural_support=support,
        capture_efficiency=capture_efficiency,
        observed_library_totals=lib,
        detected_counts=det,
        regime_labels=labels,
        latent_truth_hash=_latent_hash(latent),
        counts_hash=_csr_hash(counts),
    )
