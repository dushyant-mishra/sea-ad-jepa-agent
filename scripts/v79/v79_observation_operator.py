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
_CELL_BLOCK = 128


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


def _stack_csr_blocks(blocks: list[sparse.csr_matrix], shape: tuple[int, int]) -> sparse.csr_matrix:
    if not blocks:
        return sparse.csr_matrix(shape, dtype=np.int64)
    return sparse.vstack(blocks, format="csr", dtype=np.int64)


def observe_latent_biology(latent: LatentBiology, authority: Mapping[str, Any] | ObservationAuthority,
                           regime_labels: np.ndarray, seed: int) -> ObservationResult:
    """Observe a latent world without registry-scale dense count/rate temporaries.

    Sampling order and float64 rate arithmetic are preserved.  The independent-thinning path
    consumes the same NumPy RNG stream in row-major cell blocks; the conditional-multinomial path
    preserves its original row-wise draw order.  Only materialization changes: sampled blocks are
    converted immediately to CSR rather than accumulating a full int64 cell x gene matrix.
    """
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
    regime_index = np.asarray([regime_to_ix[x] for x in labels], dtype=np.int64)
    # The support matrix is retained in the public result contract, but all larger numeric
    # temporaries are block-local.
    support = support_table[regime_index]
    cap_mean = np.asarray(a.capture_log_mean, dtype=np.float64)[regime_index]
    cap_sd = np.asarray(a.capture_log_sd, dtype=np.float64)[regime_index]
    capture_efficiency = np.exp(rng.normal(cap_mean, cap_sd))
    propensity = np.asarray(a.gene_propensity, dtype=np.float64)

    blocks: list[sparse.csr_matrix] = []
    if a.realization_family == "independent_thinning":
        for lo in range(0, n_cells, _CELL_BLOCK):
            hi = min(lo + _CELL_BLOCK, n_cells)
            base = (np.asarray(latent.latent_abundance[lo:hi], dtype=np.float64)
                    * propensity[None, :] * support[lo:hi])
            rate = base * capture_efficiency[lo:hi, None] * a.molecule_scale
            sampled = rng.poisson(np.clip(rate, 0.0, 1e8)).astype(np.int64)
            blocks.append(sparse.csr_matrix(sampled))
        counts = _stack_csr_blocks(blocks, (n_cells, n_genes))
    elif a.realization_family == "conditional_multinomial":
        biological_mass = np.asarray(latent.latent_abundance.sum(1)).ravel()
        expected_total = biological_mass * capture_efficiency * a.molecule_scale
        totals = rng.poisson(np.clip(expected_total, 0.0, 1e8))
        indptr = np.zeros(n_cells + 1, dtype=np.int64)
        indices_parts: list[np.ndarray] = []
        data_parts: list[np.ndarray] = []
        nnz = 0
        for i in range(n_cells):
            weights = (np.asarray(latent.latent_abundance[i], dtype=np.float64)
                       * propensity * support[i])
            total = int(totals[i])
            s = float(weights.sum())
            if total > 0 and s > 0:
                draw = rng.multinomial(total, weights / s)
                nz = np.flatnonzero(draw)
                if len(nz):
                    indices_parts.append(nz.astype(np.int64, copy=False))
                    data_parts.append(draw[nz].astype(np.int64, copy=False))
                    nnz += len(nz)
            indptr[i + 1] = nnz
        indices = np.concatenate(indices_parts) if indices_parts else np.empty(0, dtype=np.int64)
        data = np.concatenate(data_parts) if data_parts else np.empty(0, dtype=np.int64)
        counts = sparse.csr_matrix((data, indices, indptr), shape=(n_cells, n_genes))
    else:  # pragma: no cover - validator prevents this
        raise ValueError("unsupported realization family")

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
