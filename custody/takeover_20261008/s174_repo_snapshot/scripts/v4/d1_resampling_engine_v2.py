#!/usr/bin/env python3
"""Incremental, fail-closed D1 resampling engine V2.

Repairs the preserved V1 engine in four ways:

- model states are assumed to come from a frozen archive, never fresh forwards;
- real donor bootstrap uses precomputed donor sufficient statistics;
- each expensive null replicate is generated exactly once and reused for both
  parallel analysis and null subspace stability;
- sequential doubling stops only when *all decision-bearing endpoint estimates*
  have sufficient Monte Carlo precision and the discrete D decisions are
  concordant across deterministic replicate batches. Hitting the ceiling without
  precision is a STOP.

The scientific D rule remains the frozen donor/operator-preserving PA +
donor-block leading-prefix rule.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.stats import t as student_t

from d1_real_data_derivation_core_v1 import (
    INSUFFICIENT_MC,
    STOP_NO_STABLE_RANK,
    block_boundary_ranks,
    degenerate_blocks,
    derive_D_PA,
    derive_production_D,
    deterministic_eigendecomposition,
    entropy_effective_rank,
    participation_effective_rank,
    projection_overlap,
    sequential_doubling_schedule,
    stratum_rng,
)

SCHEMA = "D1_RESAMPLING_ENGINE_V2"
STATE_SCHEMA = "D1_RESAMPLING_STATE_V2"
STOP_RESAMPLING_INPUT = "STOP_D1_V2_RESAMPLING_INPUT"
STOP_RESAMPLING_STATE_DRIFT = "STOP_D1_V2_RESAMPLING_STATE_DRIFT"
STOP_MC_DECISION_UNSTABLE = "STOP_D1_V2_MONTE_CARLO_DECISION_UNSTABLE"


@dataclass
class MomentSummary:
    weight_sum: float
    mean: np.ndarray
    scatter: np.ndarray
    rows: int

    def covariance(self) -> np.ndarray:
        if self.weight_sum <= 0:
            raise ValueError(f"{STOP_RESAMPLING_INPUT}: zero moment mass")
        cov = self.scatter / self.weight_sum
        return 0.5 * (cov + cov.T)


def _empty_summary(dimension: int) -> MomentSummary:
    return MomentSummary(
        0.0,
        np.zeros(int(dimension), dtype=np.float64),
        np.zeros((int(dimension), int(dimension)), dtype=np.float64),
        0,
    )


def summary_from_block(states: np.ndarray, weights: np.ndarray) -> MomentSummary:
    x = np.asarray(states, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64).reshape(-1)
    if x.ndim != 2 or x.shape[0] != w.size:
        raise ValueError(f"{STOP_RESAMPLING_INPUT}: states/weights")
    if x.shape[0] == 0:
        return _empty_summary(x.shape[1])
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(w)):
        raise ValueError(f"{STOP_RESAMPLING_INPUT}: nonfinite")
    if np.any(w < 0):
        raise ValueError(f"{STOP_RESAMPLING_INPUT}: negative weight")
    mass = float(w.sum())
    if mass <= 0:
        return _empty_summary(x.shape[1])
    mean = (w[:, None] * x).sum(axis=0) / mass
    centered = x - mean
    scatter = (centered * w[:, None]).T @ centered
    return MomentSummary(mass, mean, scatter, int(x.shape[0]))


def merge_summaries(left: MomentSummary, right: MomentSummary) -> MomentSummary:
    if left.mean.shape != right.mean.shape:
        raise ValueError(f"{STOP_RESAMPLING_INPUT}: summary dimensions")
    if left.weight_sum <= 0:
        return MomentSummary(
            right.weight_sum, right.mean.copy(), right.scatter.copy(), right.rows)
    if right.weight_sum <= 0:
        return MomentSummary(
            left.weight_sum, left.mean.copy(), left.scatter.copy(), left.rows)
    total = left.weight_sum + right.weight_sum
    delta = right.mean - left.mean
    mean = left.mean + (right.weight_sum / total) * delta
    scatter = (
        left.scatter + right.scatter
        + (left.weight_sum * right.weight_sum / total) * np.outer(delta, delta)
    )
    return MomentSummary(total, mean, scatter, left.rows + right.rows)


def merge_many(summaries: Sequence[MomentSummary], dimension: int) -> MomentSummary:
    out = _empty_summary(dimension)
    for summary in summaries:
        out = merge_summaries(out, summary)
    return out


def build_real_donor_moment_bank(source: Any, dimension: int) -> dict[str, MomentSummary]:
    bank: dict[str, MomentSummary] = {}
    rows = 0
    for donor, operator in source.strata():
        states, weights = source.load(donor, operator)
        block = summary_from_block(states, weights)
        donor = str(donor)
        bank[donor] = merge_summaries(
            bank.get(donor, _empty_summary(dimension)), block)
        rows += int(states.shape[0])
    if not bank:
        raise ValueError(f"{STOP_RESAMPLING_INPUT}: no donors")
    if hasattr(source, "total_cells") and int(source.total_cells()) != rows:
        raise ValueError(f"{STOP_RESAMPLING_INPUT}: source row drift")
    return bank


def covariance_from_donor_sample(
    bank: Mapping[str, MomentSummary], sample: Sequence[str], dimension: int
) -> np.ndarray:
    summaries = []
    for donor in sample:
        key = str(donor)
        if key not in bank:
            raise ValueError(f"{STOP_RESAMPLING_INPUT}: unknown donor {key}")
        summaries.append(bank[key])
    return merge_many(summaries, dimension).covariance()


def _donor_bootstrap_sample(donors: Sequence[str], namespace: str, replicate: int) -> list[str]:
    rng = stratum_rng(namespace, replicate, "__donor_block__", 0)
    roster = list(donors)
    indices = rng.integers(0, len(roster), size=len(roster))
    return [roster[int(i)] for i in indices]


def _permute_block_float(states: np.ndarray, *, namespace: str, replicate: int,
                         donor: str, operator: int) -> np.ndarray:
    """Independent coordinate permutations without forcing archive bytes to float64."""
    block = np.asarray(states)
    if block.ndim != 2:
        raise ValueError(f"{STOP_RESAMPLING_INPUT}: state block")
    rng = stratum_rng(namespace, replicate, str(donor), int(operator))
    out = np.empty_like(block)
    for j in range(block.shape[1]):
        out[:, j] = block[rng.permutation(block.shape[0]), j]
    return out


def build_null_donor_moment_bank(
    source: Any, dimension: int, *, namespace: str, replicate: int
) -> dict[str, MomentSummary]:
    """One expensive full-state pass for one null replicate."""
    bank: dict[str, MomentSummary] = {}
    for donor, operator in source.strata():
        states, weights = source.load(donor, operator)
        permuted = _permute_block_float(
            states, namespace=namespace, replicate=replicate,
            donor=str(donor), operator=int(operator))
        block = summary_from_block(permuted, weights)
        donor = str(donor)
        bank[donor] = merge_summaries(
            bank.get(donor, _empty_summary(dimension)), block)
    return bank


def _eigen_from_bank(
    bank: Mapping[str, MomentSummary], dimension: int,
    sample: Sequence[str] | None = None,
) -> dict[str, Any]:
    donors = sorted(bank)
    covariance = covariance_from_donor_sample(
        bank, donors if sample is None else sample, dimension)
    return deterministic_eigendecomposition(covariance)


def _batch_endpoint_precision(
    values: np.ndarray, *, quantile: float, confidence_level: float,
    target_half_width: float, batches: int = 8,
) -> dict[str, Any]:
    """Batch-means Monte Carlo error for a quantile endpoint.

    Replicate IDs are assigned to interleaved deterministic batches. Each batch
    estimates the same endpoint. A Student-t interval over the batch endpoint
    estimates measures computational Monte Carlo error, not biological/null
    distribution spread. The rule is applied elementwise and the maximum
    endpoint half-width carries the gate.
    """
    arr = np.asarray(values, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr[:, None]
    n = arr.shape[0]
    if n < batches * 4:
        return {
            "met": False, "reason": "too_few_replicates_for_batch_precision",
            "replicates": n, "max_half_width": float("inf"),
        }
    estimates = []
    for batch in range(batches):
        take = np.arange(n) % batches == batch
        if int(take.sum()) < 4:
            return {
                "met": False, "reason": "batch_too_small",
                "replicates": n, "max_half_width": float("inf"),
            }
        estimates.append(np.quantile(arr[take], quantile, axis=0))
    batch_est = np.stack(estimates, axis=0)
    se = batch_est.std(axis=0, ddof=1) / math.sqrt(batches)
    critical = float(student_t.ppf(
        0.5 + 0.5 * float(confidence_level), df=batches - 1))
    half = critical * se
    full = np.quantile(arr, quantile, axis=0)
    return {
        "met": bool(np.all(np.isfinite(half)) and np.max(half) <= target_half_width),
        "replicates": n,
        "batches": batches,
        "quantile": float(quantile),
        "estimate": np.asarray(full).tolist(),
        "half_width": np.asarray(half).tolist(),
        "max_half_width": float(np.max(half)),
        "target_half_width": float(target_half_width),
        "method": "8_interleaved_batch_quantile_t_interval",
    }


def _decision_from_arrays(
    *, observed_eigenvalues: np.ndarray, null_spectra: np.ndarray,
    real_overlaps: np.ndarray, null_overlaps: np.ndarray,
    real_eigengaps: np.ndarray, confidence_level: float,
) -> dict[str, Any]:
    null_env = np.quantile(null_spectra, confidence_level, axis=0)
    pa = derive_D_PA(observed_eigenvalues, null_env)
    if int(pa["D_PA"]) < 1:
        return {
            "D": None, "D_PA": 0, "terminal": STOP_NO_STABLE_RANK,
            "null_upper_envelope": null_env,
        }
    max_rank = int(pa["D_PA"])
    alpha = 1.0 - float(confidence_level)
    real_lower = np.quantile(real_overlaps[:, :max_rank], alpha / 2.0, axis=0)
    null_upper = np.quantile(
        null_overlaps[:, :max_rank], 1.0 - alpha / 2.0, axis=0)
    separated = [bool(a > b) for a, b in zip(real_lower, null_upper)]
    observed_gaps = observed_eigenvalues[:-1] - observed_eigenvalues[1:]
    gap_upper = np.quantile(real_eigengaps, 1.0 - alpha / 2.0, axis=0)
    gap_lower = 2.0 * observed_gaps - gap_upper
    blocks = degenerate_blocks(
        observed_eigenvalues, gap_interval_lower=gap_lower)
    try:
        d = derive_production_D(
            D_PA=max_rank,
            stability_separated_by_rank=separated,
            degeneracy_blocks=blocks["blocks"],
        )
        terminal = "PASS_D1_D_DERIVATION"
        D = int(d["D"])
    except AssertionError as error:
        terminal = str(error)
        D = None
    return {
        "D": D,
        "D_PA": max_rank,
        "terminal": terminal,
        "null_upper_envelope": null_env,
        "real_lower": real_lower,
        "null_upper": null_upper,
        "separated": separated,
        "gap_lower": gap_lower,
        "degeneracy_blocks": blocks["blocks"],
        "admissible_ranks": [
            r for r in block_boundary_ranks(blocks["blocks"]) if r <= max_rank],
    }


def _decision_concordance(
    *, observed_eigenvalues: np.ndarray, null_spectra: np.ndarray,
    real_overlaps: np.ndarray, null_overlaps: np.ndarray,
    real_eigengaps: np.ndarray, confidence_level: float, batches: int = 8,
) -> dict[str, Any]:
    full = _decision_from_arrays(
        observed_eigenvalues=observed_eigenvalues,
        null_spectra=null_spectra,
        real_overlaps=real_overlaps,
        null_overlaps=null_overlaps,
        real_eigengaps=real_eigengaps,
        confidence_level=confidence_level,
    )
    signatures = []
    n = null_spectra.shape[0]
    if n < batches * 4:
        return {"concordant": False, "full": full, "batch_signatures": []}
    for batch in range(batches):
        take = np.arange(n) % batches == batch
        decision = _decision_from_arrays(
            observed_eigenvalues=observed_eigenvalues,
            null_spectra=null_spectra[take],
            real_overlaps=real_overlaps[take],
            null_overlaps=null_overlaps[take],
            real_eigengaps=real_eigengaps[take],
            confidence_level=confidence_level,
        )
        signatures.append({
            "D": decision["D"],
            "D_PA": decision["D_PA"],
            "separated": decision.get("separated"),
            "degeneracy_blocks": decision.get("degeneracy_blocks"),
        })
    full_signature = {
        "D": full["D"],
        "D_PA": full["D_PA"],
        "separated": full.get("separated"),
        "degeneracy_blocks": full.get("degeneracy_blocks"),
    }
    return {
        "concordant": all(sig == full_signature for sig in signatures),
        "full": full,
        "batch_signatures": signatures,
    }


def _state_paths(directory: Path) -> tuple[Path, Path]:
    return directory / "D1_RESAMPLING_STATE_V2.npz", directory / "D1_RESAMPLING_STATE_V2.json"


def _save_state(
    directory: Path, *, metadata: Mapping[str, Any],
    null_spectra: np.ndarray, real_overlaps: np.ndarray,
    null_overlaps: np.ndarray, real_eigengaps: np.ndarray,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    npz, js = _state_paths(directory)
    tmp_npz = npz.with_suffix(".npz.tmp")
    tmp_js = js.with_suffix(".json.tmp")
    with tmp_npz.open("wb") as handle:
        np.savez(
            handle,
            null_spectra=null_spectra,
            real_overlaps=real_overlaps,
            null_overlaps=null_overlaps,
            real_eigengaps=real_eigengaps,
        )
    digest = hashlib.sha256(tmp_npz.read_bytes()).hexdigest()
    payload = dict(metadata)
    payload.update({
        "schema": STATE_SCHEMA,
        "replicates": int(null_spectra.shape[0]),
        "npz_sha256": digest,
    })
    tmp_js.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp_npz, npz)
    os.replace(tmp_js, js)


def _load_state(directory: Path, expected_metadata: Mapping[str, Any]) -> dict[str, Any] | None:
    npz, js = _state_paths(directory)
    if not npz.is_file() and not js.is_file():
        return None
    if not npz.is_file() or not js.is_file():
        raise ValueError(f"{STOP_RESAMPLING_STATE_DRIFT}: partial state")
    payload = json.loads(js.read_text(encoding="utf-8"))
    if payload.get("schema") != STATE_SCHEMA:
        raise ValueError(f"{STOP_RESAMPLING_STATE_DRIFT}: schema")
    for key, value in expected_metadata.items():
        if payload.get(key) != value:
            raise ValueError(f"{STOP_RESAMPLING_STATE_DRIFT}: {key}")
    actual = hashlib.sha256(npz.read_bytes()).hexdigest()
    if actual != payload.get("npz_sha256"):
        raise ValueError(f"{STOP_RESAMPLING_STATE_DRIFT}: npz hash")
    data = np.load(npz, allow_pickle=False)
    out = {k: data[k] for k in data.files}
    if any(v.shape[0] != int(payload["replicates"]) for v in out.values()):
        raise ValueError(f"{STOP_RESAMPLING_STATE_DRIFT}: replicate count")
    return {"metadata": payload, **out}


def derive_D_incremental(
    source: Any, dimension: int, *, archive_root_sha256: str,
    rng_namespace: str, confidence_level: float = 0.95,
    minimum_replicates: int = 64, maximum_replicates: int = 8192,
    precision_target_half_width: float = 0.01, doubling_factor: int = 2,
    state_dir: Path | str | None = None,
) -> dict[str, Any]:
    if int(dimension) <= 0:
        raise ValueError(f"{STOP_RESAMPLING_INPUT}: dimension")
    real_bank = build_real_donor_moment_bank(source, dimension)
    donors = sorted(real_bank)
    observed = _eigen_from_bank(real_bank, dimension)
    p = int(dimension)
    schedule = sequential_doubling_schedule(
        minimum_replicates=minimum_replicates,
        maximum_replicates=maximum_replicates,
        doubling_factor=doubling_factor,
    )
    metadata = {
        "archive_root_sha256": str(archive_root_sha256),
        "rng_namespace": str(rng_namespace),
        "dimension": p,
        "confidence_level": float(confidence_level),
        "precision_target_half_width": float(precision_target_half_width),
    }

    null_spectra = np.empty((0, p), dtype=np.float64)
    real_overlaps = np.empty((0, p), dtype=np.float64)
    null_overlaps = np.empty((0, p), dtype=np.float64)
    real_eigengaps = np.empty((0, max(0, p - 1)), dtype=np.float64)
    state_path = Path(state_dir) if state_dir is not None else None
    if state_path is not None:
        loaded = _load_state(state_path, metadata)
        if loaded is not None:
            null_spectra = loaded["null_spectra"]
            real_overlaps = loaded["real_overlaps"]
            null_overlaps = loaded["null_overlaps"]
            real_eigengaps = loaded["real_eigengaps"]

    stage_reports = []
    for target in schedule:
        start = int(null_spectra.shape[0])
        if start > target:
            continue
        new_null = []
        new_real_overlap = []
        new_null_overlap = []
        new_real_gaps = []
        for replicate in range(start, target):
            real_sample = _donor_bootstrap_sample(
                donors, rng_namespace + "|real-bootstrap", replicate)
            real_eigen = _eigen_from_bank(real_bank, p, sample=real_sample)
            new_real_gaps.append(
                real_eigen["eigenvalues"][:-1] - real_eigen["eigenvalues"][1:])
            new_real_overlap.append([
                projection_overlap(
                    observed["eigenvectors"][:, :rank],
                    real_eigen["eigenvectors"][:, :rank])
                for rank in range(1, p + 1)
            ])

            null_bank = build_null_donor_moment_bank(
                source, p, namespace=rng_namespace + "|coordinate-null",
                replicate=replicate)
            null_eigen = _eigen_from_bank(null_bank, p)
            new_null.append(null_eigen["eigenvalues"])

            null_sample = _donor_bootstrap_sample(
                donors, rng_namespace + "|null-bootstrap", replicate)
            null_boot = _eigen_from_bank(null_bank, p, sample=null_sample)
            new_null_overlap.append([
                projection_overlap(
                    observed["eigenvectors"][:, :rank],
                    null_boot["eigenvectors"][:, :rank])
                for rank in range(1, p + 1)
            ])

        if new_null:
            null_spectra = np.concatenate(
                [null_spectra, np.asarray(new_null, dtype=np.float64)], axis=0)
            real_overlaps = np.concatenate(
                [real_overlaps, np.asarray(new_real_overlap, dtype=np.float64)], axis=0)
            null_overlaps = np.concatenate(
                [null_overlaps, np.asarray(new_null_overlap, dtype=np.float64)], axis=0)
            real_eigengaps = np.concatenate(
                [real_eigengaps, np.asarray(new_real_gaps, dtype=np.float64)], axis=0)
        if state_path is not None:
            _save_state(
                state_path, metadata=metadata,
                null_spectra=null_spectra, real_overlaps=real_overlaps,
                null_overlaps=null_overlaps, real_eigengaps=real_eigengaps)

        alpha = 1.0 - float(confidence_level)
        precision = {
            "null_eigenvalue_upper": _batch_endpoint_precision(
                null_spectra, quantile=confidence_level,
                confidence_level=confidence_level,
                target_half_width=precision_target_half_width),
            "real_overlap_lower": _batch_endpoint_precision(
                real_overlaps, quantile=alpha / 2.0,
                confidence_level=confidence_level,
                target_half_width=precision_target_half_width),
            "null_overlap_upper": _batch_endpoint_precision(
                null_overlaps, quantile=1.0 - alpha / 2.0,
                confidence_level=confidence_level,
                target_half_width=precision_target_half_width),
            "eigengap_bootstrap_upper": _batch_endpoint_precision(
                real_eigengaps, quantile=1.0 - alpha / 2.0,
                confidence_level=confidence_level,
                target_half_width=precision_target_half_width)
            if p > 1 else {
                "met": True, "max_half_width": 0.0, "replicates": int(target),
                "reason": "dimension_one_no_eigengap",
            },
        }
        concordance = _decision_concordance(
            observed_eigenvalues=observed["eigenvalues"],
            null_spectra=null_spectra,
            real_overlaps=real_overlaps,
            null_overlaps=null_overlaps,
            real_eigengaps=real_eigengaps,
            confidence_level=confidence_level,
        )
        precision_met = all(bool(v["met"]) for v in precision.values())
        stage = {
            "replicates": int(target),
            "precision": precision,
            "precision_met": precision_met,
            "decision_concordance": concordance,
        }
        stage_reports.append(stage)
        if precision_met and concordance["concordant"]:
            decision = concordance["full"]
            if decision["D"] is None:
                raise AssertionError(decision["terminal"])
            entropy = entropy_effective_rank(observed["eigenvalues"])
            participation = participation_effective_rank(observed["eigenvalues"])
            return {
                "schema": SCHEMA,
                "terminal": "PASS_D1_V2_D_DERIVATION",
                "D": int(decision["D"]),
                "K": int(decision["D"]),
                "D_PA": int(decision["D_PA"]),
                "eigenvalues": observed["eigenvalues"].tolist(),
                "eigenvectors_leading": observed["eigenvectors"][:, :int(decision["D"])].tolist(),
                "mean": merge_many(list(real_bank.values()), p).mean.tolist(),
                "null_upper_envelope": np.asarray(
                    decision["null_upper_envelope"]).tolist(),
                "real_overlap_lower": np.asarray(decision["real_lower"]).tolist(),
                "null_overlap_upper": np.asarray(decision["null_upper"]).tolist(),
                "degeneracy_blocks": decision["degeneracy_blocks"],
                "admissible_ranks": decision["admissible_ranks"],
                "separation_flags": decision["separated"],
                "monte_carlo_replicates": int(target),
                "monte_carlo_stage_reports": stage_reports,
                "effective_rank_diagnostics": {
                    "entropy_effective_rank": float(entropy["value"]),
                    "participation_effective_rank": float(participation["value"]),
                    "defines_D": False,
                },
                "archive_root_sha256": str(archive_root_sha256),
            }

    final = stage_reports[-1] if stage_reports else {}
    raise AssertionError(
        f"{INSUFFICIENT_MC}: reached {maximum_replicates} replicates without "
        f"all endpoint precision and decision concordance; final={final}")
