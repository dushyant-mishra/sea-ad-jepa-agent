#!/usr/bin/env python3
"""D1 real-data derivation core: streaming estimators and fail-closed D logic.

Mechanics only. Nothing in this module reads biological data or decides a
production value on its own; it provides the arithmetic that the audit and
derivation drivers call under an explicit population class.

The governing rule this module enforces structurally: a production
data-adaptive D1 quantity may only be emitted from the complete lawful fit
population (104 donors / 4,553,407 cells / 42 operators). Synthetic fixtures,
the historical 4,540-cell biology cohort, and the 50,000-cell discovery sample
can each drive every estimator here, but their provenance carries a population
class that `emit_production_parameter` refuses. That refusal is a property of
the provenance object rather than a naming convention, so a synthetic result
cannot become a production parameter by being renamed.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Iterator, Mapping, Sequence

import numpy as np

# ---------------------------------------------------------------------------
# Population classes. Only one of these may produce a production parameter.
# ---------------------------------------------------------------------------
PRODUCTION_FULL_FIT = "PRODUCTION_FULL_FIT"
MECHANICS_ONLY = "MECHANICS_ONLY"
AUXILIARY_REAL_50K = "AUXILIARY_REAL_50K"
HISTORICAL_BIOLOGY_COHORT_4540 = "HISTORICAL_BIOLOGY_COHORT_4540"
FORBIDDEN_PROTECTED = "FORBIDDEN_PROTECTED"

POPULATION_CLASSES = (
    PRODUCTION_FULL_FIT,
    MECHANICS_ONLY,
    AUXILIARY_REAL_50K,
    HISTORICAL_BIOLOGY_COHORT_4540,
    FORBIDDEN_PROTECTED,
)

# Exactly one class may back a production parameter.
PRODUCTION_ELIGIBLE_CLASSES = (PRODUCTION_FULL_FIT,)

# Authority expectations, verified by the Phase 0 audit rather than trusted.
EXPECTED_FIT_DONORS = 104
EXPECTED_FIT_CELLS = 4553407
EXPECTED_OPERATORS = 42
EXPECTED_MOLECULAR_ADDRESSES = 41238
ALLOWED_SOURCE_FAMILIES = ("HVS", "NPH52", "SEA_AD")
LAWFUL_PARTITION = "reader_fit"
FORBIDDEN_PARTITIONS = (
    "reader_validation", "reader_oracle", "development", "dev", "sealed",
    "sealed_holdout", "whole_study_external_holdout", "pathology", "held_out",
)

# Values that exist in historical authorities and must not be reused as D1
# production choices. Checked against the config and against emitted values.
PROHIBITED_HISTORICAL_VALUES = {
    "retained_svd_components": 50,
    "knn_k_15": 15, "knn_k_30": 30, "knn_k_60": 60, "knn_k_120": 120,
    "candidate_search_rank": 320,
    "feature_sketch_dimension": 512,
    "donor_resamples": 256,
    "matched_null_replicates": 256,
}

STOP_NON_CONTIGUOUS = "STOP_D1_PARALLEL_ANALYSIS_NON_CONTIGUOUS_SURVIVAL"
STOP_NO_STABLE_RANK = "STOP_D1_NO_STABLE_LEADING_RANK__NO_FALLBACK_D"
STOP_NOT_PRODUCTION_POPULATION = "STOP_D1_NOT_PRODUCTION_POPULATION"
STOP_TEACHER_GATE_CLOSED = "STOP_D1_TEACHER_GATE_CLOSED"
STOP_PROTECTED_POPULATION = "STOP_D1_PROTECTED_POPULATION_ACCESS"
INSUFFICIENT_MC = "INSUFFICIENT_MONTE_CARLO_PRECISION"


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class D1Provenance:
    """Where a number came from, in a form that gates its use.

    `population_class` is not decoration. `emit_production_parameter` reads it,
    so a mechanics result cannot be promoted by relabelling the artifact.
    """

    statistic_id: str
    population_class: str
    formula_version: str
    input_roots: Mapping[str, str] = field(default_factory=dict)
    donors: int | None = None
    cells: int | None = None
    operators: int | None = None
    teacher_checkpoint_root: str | None = None
    teacher_readout_contract_hash: str | None = None
    rng_namespace: str | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        if self.population_class not in POPULATION_CLASSES:
            raise ValueError("unknown population_class: %r" % (self.population_class,))

    def is_production_eligible(self) -> bool:
        """True only for the complete lawful fit population at exact counts."""
        if self.population_class not in PRODUCTION_ELIGIBLE_CLASSES:
            return False
        return (self.donors == EXPECTED_FIT_DONORS
                and self.cells == EXPECTED_FIT_CELLS
                and self.operators == EXPECTED_OPERATORS)

    def as_dict(self) -> dict[str, Any]:
        return {
            "statistic_id": self.statistic_id,
            "population_class": self.population_class,
            "formula_version": self.formula_version,
            "input_roots": dict(self.input_roots),
            "donors": self.donors,
            "cells": self.cells,
            "operators": self.operators,
            "teacher_checkpoint_root": self.teacher_checkpoint_root,
            "teacher_readout_contract_hash": self.teacher_readout_contract_hash,
            "rng_namespace": self.rng_namespace,
            "notes": self.notes,
        }


def emit_production_parameter(*, parameter_id: str, value: Any,
                              provenance: D1Provenance,
                              teacher_gate_open: bool,
                              diagnostics: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """The only lawful way to produce a production D1 parameter record.

    Fails closed on a non-production population, on a closed teacher gate, and
    on a value that collides with a prohibited historical constant for a
    parameter whose derivation must be data-adaptive.
    """
    if provenance.population_class == FORBIDDEN_PROTECTED:
        raise PermissionError("%s: %s" % (STOP_PROTECTED_POPULATION, parameter_id))
    if not provenance.is_production_eligible():
        raise PermissionError(
            "%s: %s may not be emitted from population_class=%s with "
            "donors=%r cells=%r operators=%r"
            % (STOP_NOT_PRODUCTION_POPULATION, parameter_id,
               provenance.population_class, provenance.donors,
               provenance.cells, provenance.operators))
    if not teacher_gate_open:
        raise PermissionError("%s: %s" % (STOP_TEACHER_GATE_CLOSED, parameter_id))
    return {
        "schema": "d1-production-parameter-v1",
        "parameter_id": parameter_id,
        "value": value,
        "provenance": provenance.as_dict(),
        "diagnostics": dict(diagnostics or {}),
    }


def mechanics_result(*, statistic_id: str, value: Any,
                     diagnostics: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """A mechanics-only result, labelled so it cannot be mistaken for production."""
    return {
        "schema": "d1-mechanics-only-result-v1",
        "population_class": MECHANICS_ONLY,
        "statistic_id": statistic_id,
        "value": value,
        "diagnostics": dict(diagnostics or {}),
        "production_use": "PROHIBITED",
    }


# ---------------------------------------------------------------------------
# Donor-primary weighting: a_dc = 1 / (|O_d| * n_do)
# ---------------------------------------------------------------------------
def derive_donor_operator_weights(
    counts: Mapping[tuple[str, int], int]
) -> dict[str, Any]:
    """Derive |O_d|, n_do and the cell weight from full real fit metadata.

    `counts` maps (donor_id, operator_index) -> lawful cell count. Consequences
    of `a_dc = 1/(|O_d| n_do)`, both asserted below: every donor carries total
    mass exactly 1, and each operator within a donor carries exactly 1/|O_d|.
    That is what makes the weighting donor-primary rather than cell-primary.
    """
    if not counts:
        raise ValueError("empty donor x operator counts")
    operators_by_donor: dict[str, set[int]] = {}
    for (donor, operator), n in counts.items():
        if int(n) <= 0:
            raise ValueError("non-positive n_do for (%r,%r)" % (donor, operator))
        operators_by_donor.setdefault(str(donor), set()).add(int(operator))

    cell_weight: dict[tuple[str, int], float] = {}
    operator_mass: dict[tuple[str, int], float] = {}
    donor_mass: dict[str, float] = {}
    for (donor, operator), n in counts.items():
        k = len(operators_by_donor[str(donor)])
        a_dc = 1.0 / (k * float(n))
        cell_weight[(str(donor), int(operator))] = a_dc
        mass = float(n) * a_dc                      # = 1/k
        operator_mass[(str(donor), int(operator))] = mass
        donor_mass[str(donor)] = donor_mass.get(str(donor), 0.0) + mass
    return {
        "operators_by_donor": {d: sorted(v) for d, v in operators_by_donor.items()},
        "operator_count_by_donor": {d: len(v) for d, v in operators_by_donor.items()},
        "n_do": {k: int(v) for k, v in counts.items()},
        "cell_weight_a_dc": cell_weight,
        "operator_mass_within_donor": operator_mass,
        "donor_mass": donor_mass,
        "donors": len(operators_by_donor),
        "operators": len({o for _, o in counts}),
        "cells": int(sum(int(v) for v in counts.values())),
    }


def assert_donor_primary_masses(weights: Mapping[str, Any], *, atol: float = 1e-9) -> dict[str, float]:
    """Every donor has mass 1; every operator within a donor has mass 1/|O_d|."""
    worst_donor = 0.0
    for donor, mass in weights["donor_mass"].items():
        worst_donor = max(worst_donor, abs(float(mass) - 1.0))
    worst_operator = 0.0
    for (donor, operator), mass in weights["operator_mass_within_donor"].items():
        k = weights["operator_count_by_donor"][donor]
        worst_operator = max(worst_operator, abs(float(mass) - 1.0 / k))
    if worst_donor > atol:
        raise AssertionError("STOP_D1_DONOR_MASS_NOT_EQUAL: max deviation %.3e" % worst_donor)
    if worst_operator > atol:
        raise AssertionError("STOP_D1_OPERATOR_MASS_NOT_EQUAL: max deviation %.3e" % worst_operator)
    return {"max_donor_mass_deviation": worst_donor,
            "max_operator_mass_deviation": worst_operator}


# ---------------------------------------------------------------------------
# Streaming weighted moments
# ---------------------------------------------------------------------------
class WeightedMomentAccumulator:
    """Numerically stable streaming weighted mean and covariance.

    Uses the weighted Welford/Chan parallel form: each chunk contributes its own
    scatter about its own mean plus a between-chunk correction. Accumulating raw
    sum(w z z^T) and subtracting mu mu^T instead would lose precision by
    catastrophic cancellation when the mean is large relative to the spread,
    which is a real risk over 4,553,407 cells.
    """

    def __init__(self, dimension: int, dtype: Any = np.float64) -> None:
        if int(dimension) <= 0:
            raise ValueError("dimension must be positive")
        self.dimension = int(dimension)
        self.dtype = dtype
        self.weight_sum = 0.0
        self.mean = np.zeros(self.dimension, dtype=dtype)
        self._scatter = np.zeros((self.dimension, self.dimension), dtype=dtype)
        self.chunks = 0
        self.rows = 0

    def update(self, states: np.ndarray, weights: np.ndarray) -> "WeightedMomentAccumulator":
        states = np.asarray(states, dtype=self.dtype)
        weights = np.asarray(weights, dtype=self.dtype).reshape(-1)
        if states.ndim != 2 or states.shape[1] != self.dimension:
            raise ValueError("states must be (n, %d)" % self.dimension)
        if states.shape[0] != weights.shape[0]:
            raise ValueError("states and weights disagree in length")
        if states.shape[0] == 0:
            return self
        if not np.all(np.isfinite(states)) or not np.all(np.isfinite(weights)):
            raise ValueError("STOP_D1_NON_FINITE_INPUT")
        if np.any(weights < 0):
            raise ValueError("STOP_D1_NEGATIVE_WEIGHT")
        w_sum = float(weights.sum())
        if w_sum <= 0.0:
            return self
        chunk_mean = (weights[:, None] * states).sum(axis=0) / w_sum
        centered = states - chunk_mean
        chunk_scatter = (centered * weights[:, None]).T @ centered

        if self.weight_sum == 0.0:
            self.mean = chunk_mean
            self._scatter = chunk_scatter
        else:
            total = self.weight_sum + w_sum
            delta = chunk_mean - self.mean
            self.mean = self.mean + (w_sum / total) * delta
            self._scatter = (self._scatter + chunk_scatter
                             + (self.weight_sum * w_sum / total) * np.outer(delta, delta))
        self.weight_sum += w_sum
        self.chunks += 1
        self.rows += int(states.shape[0])
        return self

    def covariance(self) -> np.ndarray:
        if self.weight_sum <= 0.0:
            raise ValueError("no weighted mass accumulated")
        cov = self._scatter / self.weight_sum
        return 0.5 * (cov + cov.T)      # enforce exact symmetry

    def result(self) -> dict[str, Any]:
        return {"mean": self.mean.copy(), "covariance": self.covariance(),
                "weight_sum": self.weight_sum, "rows": self.rows, "chunks": self.chunks}


# ---------------------------------------------------------------------------
# Eigendecomposition and effective ranks
# ---------------------------------------------------------------------------
def deterministic_eigendecomposition(covariance: np.ndarray, *,
                                     symmetry_atol: float = 1e-10,
                                     negative_atol: float = 1e-9) -> dict[str, Any]:
    """Full symmetric eigendecomposition, descending, with deterministic signs.

    Eigenvector sign is fixed by making the component of largest magnitude
    positive, so repeated runs and bootstrap replicas are comparable without an
    arbitrary flip. Sign is a convention, not a claim: for a degenerate block
    the individual axes are still not separately identified.
    """
    cov = np.asarray(covariance, dtype=np.float64)
    if cov.ndim != 2 or cov.shape[0] != cov.shape[1]:
        raise ValueError("covariance must be square")
    asymmetry = float(np.max(np.abs(cov - cov.T))) if cov.size else 0.0
    if asymmetry > symmetry_atol:
        raise ValueError("STOP_D1_COVARIANCE_NOT_SYMMETRIC: %.3e" % asymmetry)
    cov = 0.5 * (cov + cov.T)
    values, vectors = np.linalg.eigh(cov)
    order = np.argsort(values)[::-1]
    values = values[order]
    vectors = vectors[:, order]
    most_negative = float(values.min()) if values.size else 0.0
    if most_negative < -abs(negative_atol):
        raise ValueError("STOP_D1_COVARIANCE_NOT_PSD: min eigenvalue %.3e" % most_negative)
    values = np.clip(values, 0.0, None)
    for j in range(vectors.shape[1]):
        column = vectors[:, j]
        pivot = int(np.argmax(np.abs(column)))
        if column[pivot] < 0:
            vectors[:, j] = -column
    return {"eigenvalues": values, "eigenvectors": vectors,
            "asymmetry": asymmetry, "min_raw_eigenvalue": most_negative}


def entropy_effective_rank(eigenvalues: Sequence[float]) -> dict[str, Any]:
    """exp(-sum p log p) with p = lambda / sum lambda. Diagnostic only.

    Returned with its own `statistic_id` so it cannot be silently substituted
    for the participation ratio; the two answer different questions and the
    authority forbids aliasing them.
    """
    lam = np.asarray(eigenvalues, dtype=np.float64)
    if lam.ndim != 1 or lam.size == 0:
        raise ValueError("eigenvalues must be a non-empty 1-D array")
    if np.any(lam < -1e-12):
        raise ValueError("STOP_D1_NEGATIVE_EIGENVALUE")
    lam = np.clip(lam, 0.0, None)
    total = float(lam.sum())
    if total <= 0.0:
        raise ValueError("STOP_D1_ZERO_SPECTRUM")
    p = lam / total
    nz = p[p > 0.0]
    shannon = float(-np.sum(nz * np.log(nz)))
    return {"statistic_id": "D1-P010:entropy_effective_rank",
            "role": "DIAGNOSTIC_ONLY",
            "value": float(math.exp(shannon)),
            "shannon_entropy_nats": shannon}


def participation_effective_rank(eigenvalues: Sequence[float]) -> dict[str, Any]:
    """(sum lambda)^2 / sum(lambda^2). Diagnostic only, never aliased to entropy."""
    lam = np.asarray(eigenvalues, dtype=np.float64)
    if lam.ndim != 1 or lam.size == 0:
        raise ValueError("eigenvalues must be a non-empty 1-D array")
    if np.any(lam < -1e-12):
        raise ValueError("STOP_D1_NEGATIVE_EIGENVALUE")
    lam = np.clip(lam, 0.0, None)
    denominator = float(np.sum(lam ** 2))
    if denominator <= 0.0:
        raise ValueError("STOP_D1_ZERO_SPECTRUM")
    return {"statistic_id": "D1-P011:participation_effective_rank",
            "role": "DIAGNOSTIC_ONLY",
            "value": float(float(lam.sum()) ** 2 / denominator)}


def assert_effective_ranks_not_aliased(entropy: Mapping[str, Any],
                                       participation: Mapping[str, Any]) -> dict[str, Any]:
    """Refuse to report the two effective ranks as interchangeable.

    They coincide numerically only in degenerate spectra (a flat spectrum gives
    both exactly the number of non-zero axes), so equality alone is not the
    error. Passing one where the other is expected is, and the statistic_id
    check catches that regardless of the numbers.
    """
    if entropy.get("statistic_id") != "D1-P010:entropy_effective_rank":
        raise AssertionError("STOP_D1_EFFECTIVE_RANK_ALIASED: entropy slot got %r"
                             % (entropy.get("statistic_id"),))
    if participation.get("statistic_id") != "D1-P011:participation_effective_rank":
        raise AssertionError("STOP_D1_EFFECTIVE_RANK_ALIASED: participation slot got %r"
                             % (participation.get("statistic_id"),))
    if entropy.get("role") != "DIAGNOSTIC_ONLY" or participation.get("role") != "DIAGNOSTIC_ONLY":
        raise AssertionError("STOP_D1_EFFECTIVE_RANK_NOT_DIAGNOSTIC")
    return {"entropy_effective_rank": float(entropy["value"]),
            "participation_effective_rank": float(participation["value"]),
            "aliasing": "REFUSED",
            "defines_D": False}


# ---------------------------------------------------------------------------
# Donor/operator-preserving parallel-analysis null
# ---------------------------------------------------------------------------
def stratum_rng(namespace: str, replicate: int, donor: str, operator: int) -> np.random.Generator:
    """Deterministic per-stratum generator, so a replica is reproducible.

    Seeding from a hash of the namespace and stratum identity means the null is
    reproducible from provenance alone and does not depend on iteration order.
    """
    tag = "|".join([str(namespace), str(int(replicate)), str(donor), str(int(operator))])
    digest = hashlib.sha256(tag.encode("utf-8")).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "big"))


def permute_coordinates_within_stratum(states: np.ndarray,
                                       rng: np.random.Generator) -> np.ndarray:
    """Independently permute each state coordinate among cells of one stratum.

    This preserves every coordinate's real marginal distribution and the real
    donor/operator population while destroying cell-specific cross-coordinate
    covariance -- the null the authority specifies. Permuting whole rows instead
    would preserve the covariance and produce no null at all.
    """
    block = np.asarray(states, dtype=np.float64)
    if block.ndim != 2:
        raise ValueError("states must be 2-D")
    out = np.empty_like(block)
    for j in range(block.shape[1]):
        out[:, j] = block[rng.permutation(block.shape[0]), j]
    return out


def null_eigenvalue_envelope(replica_spectra: Sequence[Sequence[float]], *,
                             confidence_level: float = 0.95) -> dict[str, Any]:
    """Upper envelope of null eigenvalues, per ordered component."""
    spectra = np.asarray(replica_spectra, dtype=np.float64)
    if spectra.ndim != 2 or spectra.shape[0] < 2:
        raise ValueError("need at least two null replicas as a 2-D array")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be in (0,1)")
    upper = np.quantile(spectra, confidence_level, axis=0)
    return {"upper_envelope": upper,
            "median": np.quantile(spectra, 0.5, axis=0),
            "replicas": int(spectra.shape[0]),
            "confidence_level": float(confidence_level)}


def derive_D_PA(observed_eigenvalues: Sequence[float],
                null_upper_envelope: Sequence[float]) -> dict[str, Any]:
    """Largest CONTIGUOUS leading rank whose eigenvalue exceeds the null envelope.

    Non-contiguous survival is a STOP, not a resumption. Skipping a failed axis
    and continuing would silently redefine D as "count of surviving axes", which
    is a different and weaker claim than "leading signal subspace of rank d".
    """
    observed = np.asarray(observed_eigenvalues, dtype=np.float64)
    envelope = np.asarray(null_upper_envelope, dtype=np.float64)
    if observed.shape != envelope.shape:
        raise ValueError("observed and envelope must have the same shape")
    if observed.ndim != 1 or observed.size == 0:
        raise ValueError("need a non-empty 1-D spectrum")
    survives = observed > envelope
    leading = 0
    for flag in survives:
        if bool(flag):
            leading += 1
        else:
            break
    if bool(np.any(survives[leading:])):
        later = [int(i) + 1 for i, f in enumerate(survives) if f and i >= leading]
        raise AssertionError(
            "%s: contiguous leading run is %d but ranks %r also exceed the null "
            "envelope; refusing to skip a failed axis and resume"
            % (STOP_NON_CONTIGUOUS, leading, later))
    return {"D_PA": int(leading),
            "survives": [bool(f) for f in survives],
            "statistic_id": "D1-P007:D_PA"}


# ---------------------------------------------------------------------------
# Donor-block bootstrap and subspace comparison
# ---------------------------------------------------------------------------
def donor_block_resample(donors: Sequence[str], rng: np.random.Generator) -> list[str]:
    """Resample donors as whole blocks, with replacement.

    Every sampled donor carries all of its lawful operator/cell rows. Resampling
    cells instead would break the donor as the independent unit and understate
    uncertainty.
    """
    roster = list(donors)
    if not roster:
        raise ValueError("empty donor roster")
    index = rng.integers(0, len(roster), size=len(roster))
    return [roster[int(i)] for i in index]


def principal_angles(basis_a: np.ndarray, basis_b: np.ndarray) -> np.ndarray:
    """Principal angles (radians, ascending) between two subspaces."""
    a = np.asarray(basis_a, dtype=np.float64)
    b = np.asarray(basis_b, dtype=np.float64)
    if a.ndim != 2 or b.ndim != 2 or a.shape[0] != b.shape[0]:
        raise ValueError("bases must be (p, k) with matching p")
    qa, _ = np.linalg.qr(a)
    qb, _ = np.linalg.qr(b)
    singular = np.linalg.svd(qa.T @ qb, compute_uv=False)
    return np.arccos(np.clip(singular, -1.0, 1.0))


def projection_overlap(basis_a: np.ndarray, basis_b: np.ndarray) -> float:
    """Normalised projection-matrix overlap in [0,1], sign- and rotation-blind.

    Equals mean(cos^2 theta) over the principal angles. Comparing projection
    matrices rather than individual eigenvectors is what makes a degenerate
    block comparable at all: inside such a block the individual axes are not
    identified, but the subspace they span is.
    """
    a = np.asarray(basis_a, dtype=np.float64)
    b = np.asarray(basis_b, dtype=np.float64)
    if a.shape[1] != b.shape[1]:
        raise ValueError("subspaces must have equal dimension")
    qa, _ = np.linalg.qr(a)
    qb, _ = np.linalg.qr(b)
    k = qa.shape[1]
    return float(np.sum((qa.T @ qb) ** 2) / k)


def degenerate_blocks(eigenvalues: Sequence[float],
                      gap_interval_lower: Sequence[float] | None = None) -> dict[str, Any]:
    """Group adjacent axes into subspaces when their eigengap may be zero.

    `gap_interval_lower[j]` is the lower bound of the resampled interval for
    gap j = lambda_j - lambda_{j+1}. When that bound is <= 0 the gap is not
    resolved and the two axes belong to one subspace. With no interval supplied
    the observed gap is used, so exactly equal eigenvalues still form a block --
    the case where individual axes are provably unidentified.
    """
    lam = np.asarray(eigenvalues, dtype=np.float64)
    if lam.ndim != 1 or lam.size == 0:
        raise ValueError("eigenvalues must be non-empty 1-D")
    gaps = lam[:-1] - lam[1:]
    lower = np.asarray(gap_interval_lower, dtype=np.float64) if gap_interval_lower is not None else gaps
    if lower.shape != gaps.shape:
        raise ValueError("gap_interval_lower must have length len(eigenvalues)-1")
    blocks: list[list[int]] = [[0]]
    for j in range(lam.size - 1):
        if float(lower[j]) <= 0.0:
            blocks[-1].append(j + 1)
        else:
            blocks.append([j + 1])
    return {"blocks": [list(b) for b in blocks],
            "block_of_axis": {int(a): i for i, b in enumerate(blocks) for a in b},
            "gaps": gaps,
            "multi_axis_blocks": [list(b) for b in blocks if len(b) > 1],
            "statistic_id": "D1-P013:component_degeneracy_blocks"}


def rank_stability_separates(observed_lower: Sequence[float],
                             null_upper: Sequence[float]) -> list[bool]:
    """Per leading rank: does the real lower bound clear the null upper bound?"""
    obs = np.asarray(observed_lower, dtype=np.float64)
    null = np.asarray(null_upper, dtype=np.float64)
    if obs.shape != null.shape:
        raise ValueError("bounds must have the same shape")
    return [bool(o > n) for o, n in zip(obs, null)]


def derive_production_D(*, D_PA: int, stability_separated_by_rank: Sequence[bool]) -> dict[str, Any]:
    """D = largest leading d <= D_PA separated from the null for every rank 1..d.

    No fallback. If rank 1 is not separated there is no D, and D1 emits a STOP
    for program decomposition rather than substituting a default.
    """
    if int(D_PA) < 0:
        raise ValueError("D_PA must be non-negative")
    flags = [bool(f) for f in stability_separated_by_rank]
    limit = min(int(D_PA), len(flags))
    d = 0
    for rank in range(limit):
        if flags[rank]:
            d = rank + 1
        else:
            break
    if d <= 0:
        raise AssertionError(
            "%s: D_PA=%d, separation flags=%r; no positive leading rank is stable "
            "and no fallback D is permitted" % (STOP_NO_STABLE_RANK, int(D_PA), flags))
    return {"D": int(d), "D_PA": int(D_PA), "K": int(d),
            "separation_flags": flags,
            "statistic_id": "D1-P009:D",
            "K_rule": "K=D for D1 v1; no 320, no 512, no 50-PC, no 2*D expansion"}


# ---------------------------------------------------------------------------
# Monte Carlo sequential doubling
# ---------------------------------------------------------------------------
def sequential_doubling_schedule(*, minimum_replicates: int, maximum_replicates: int,
                                 doubling_factor: int = 2) -> list[int]:
    """Deterministic replicate schedule. Never inherits a historical count."""
    if minimum_replicates < 2 or maximum_replicates < minimum_replicates:
        raise ValueError("invalid replicate bounds")
    if doubling_factor < 2:
        raise ValueError("doubling_factor must be at least 2")
    schedule, n = [], int(minimum_replicates)
    while n < int(maximum_replicates):
        schedule.append(n)
        n *= int(doubling_factor)
    schedule.append(int(maximum_replicates))
    return schedule


def monte_carlo_precision_met(values: Sequence[float], *, confidence_level: float,
                              precision_target_half_width: float) -> dict[str, Any]:
    """Has the resampled interval reached the predeclared half-width?"""
    arr = np.asarray(values, dtype=np.float64)
    if arr.size < 2:
        return {"met": False, "reason": "fewer than two replicates",
                "half_width": float("inf")}
    alpha = 1.0 - float(confidence_level)
    lower = float(np.quantile(arr, alpha / 2.0))
    upper = float(np.quantile(arr, 1.0 - alpha / 2.0))
    half = 0.5 * (upper - lower)
    return {"met": bool(half <= float(precision_target_half_width)),
            "lower": lower, "upper": upper, "half_width": half,
            "replicates": int(arr.size),
            "terminal_if_unmet": INSUFFICIENT_MC}


# ---------------------------------------------------------------------------
# Cell scores, percentiles and descriptive tails
# ---------------------------------------------------------------------------
def program_score(states: np.ndarray, mean: np.ndarray, direction: np.ndarray) -> np.ndarray:
    """score_cp = (z_c - mu) . v_p for an isolated axis."""
    z = np.asarray(states, dtype=np.float64)
    mu = np.asarray(mean, dtype=np.float64).reshape(-1)
    v = np.asarray(direction, dtype=np.float64).reshape(-1)
    if z.ndim != 2 or z.shape[1] != mu.size or v.size != mu.size:
        raise ValueError("shape mismatch between states, mean and direction")
    return (z - mu) @ v


def subspace_score_norm(states: np.ndarray, mean: np.ndarray, basis: np.ndarray) -> dict[str, Any]:
    """For a degenerate block, keep the block coordinates and the subspace norm.

    No preferred axis is invented inside the block, because none is identified.
    """
    z = np.asarray(states, dtype=np.float64)
    mu = np.asarray(mean, dtype=np.float64).reshape(-1)
    b = np.asarray(basis, dtype=np.float64)
    if b.ndim != 2 or b.shape[0] != mu.size:
        raise ValueError("basis must be (p, k)")
    q, _ = np.linalg.qr(b)
    coordinates = (z - mu) @ q
    return {"coordinates": coordinates,
            "subspace_norm": np.linalg.norm(coordinates, axis=1),
            "preferred_axis": None,
            "note": "block coordinates retained; no axis inside the block is identified"}


def within_donor_centered(scores: np.ndarray, donors: Sequence[str],
                          weights: np.ndarray) -> np.ndarray:
    """score minus the donor's own weighted mean score."""
    s = np.asarray(scores, dtype=np.float64).reshape(-1)
    w = np.asarray(weights, dtype=np.float64).reshape(-1)
    d = np.asarray([str(x) for x in donors])
    if not (s.size == w.size == d.size):
        raise ValueError("scores, donors and weights must align")
    out = np.empty_like(s)
    for donor in np.unique(d):
        m = d == donor
        mass = float(w[m].sum())
        if mass <= 0.0:
            raise ValueError("STOP_D1_ZERO_DONOR_MASS: %s" % donor)
        out[m] = s[m] - float((w[m] * s[m]).sum() / mass)
    return out


def weighted_quantile(values: Sequence[float], weights: Sequence[float],
                      probabilities: Sequence[float]) -> np.ndarray:
    """Weighted empirical quantiles from the full real distribution."""
    v = np.asarray(values, dtype=np.float64).reshape(-1)
    w = np.asarray(weights, dtype=np.float64).reshape(-1)
    p = np.asarray(probabilities, dtype=np.float64).reshape(-1)
    if v.size != w.size or v.size == 0:
        raise ValueError("values and weights must align and be non-empty")
    if np.any(w < 0):
        raise ValueError("STOP_D1_NEGATIVE_WEIGHT")
    if np.any((p < 0) | (p > 1)):
        raise ValueError("probabilities must be in [0,1]")
    order = np.argsort(v, kind="stable")
    v, w = v[order], w[order]
    total = float(w.sum())
    if total <= 0.0:
        raise ValueError("STOP_D1_ZERO_WEIGHT_MASS")
    cumulative = (np.cumsum(w) - 0.5 * w) / total
    return np.interp(p, cumulative, v)


def weighted_percentile_of_score(values: Sequence[float], weights: Sequence[float]) -> np.ndarray:
    """Weighted empirical percentile of each value within the distribution."""
    v = np.asarray(values, dtype=np.float64).reshape(-1)
    w = np.asarray(weights, dtype=np.float64).reshape(-1)
    if v.size != w.size or v.size == 0:
        raise ValueError("values and weights must align and be non-empty")
    order = np.argsort(v, kind="stable")
    sorted_w = w[order]
    total = float(sorted_w.sum())
    cumulative = (np.cumsum(sorted_w) - 0.5 * sorted_w) / total
    out = np.empty_like(v)
    out[order] = cumulative
    return out


def descriptive_tail_views(values: Sequence[float], weights: Sequence[float],
                           two_sided_probabilities: Sequence[float]) -> dict[str, Any]:
    """Predeclared two-sided tail views with real-data numeric cutpoints.

    The continuous ranking stays authoritative. Each view records the actual
    weighted score cutpoints, and every view is marked non-confirmatory so a
    tail cannot quietly become a PASS/FAIL threshold.
    """
    views = {}
    for prob in two_sided_probabilities:
        p = float(prob)
        if not 0.0 < p < 0.5:
            raise ValueError("two-sided tail probability must be in (0, 0.5)")
        low, high = weighted_quantile(values, weights, [p, 1.0 - p])
        views["p%g" % p] = {
            "two_sided_probability": p,
            "lower_cutpoint": float(low),
            "upper_cutpoint": float(high),
            "cutpoint_source": "weighted empirical quantile of the full real score distribution",
            "is_confirmatory_gate": False,
        }
    return {"statistic_id": "D1-P017:tail_numeric_cutpoints",
            "views": views,
            "continuous_ranking_authoritative": True,
            "descriptive_only": True}


# ---------------------------------------------------------------------------
# Molecular association with an explicit measurement mask
# ---------------------------------------------------------------------------
# Observation-state codes, taken from the authority's own `state_names` array in
# FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz, which orders them
# ['STRUCTURALLY_UNMEASURED', 'MEASURED_SCALAR', 'MEASURED_COLLISION_UNRESOLVED'].
#
# An earlier draft of this module hardcoded MEASURED_SCALAR = 0 from intuition
# rather than reading the authority. That is inverted, and it would have treated
# every structurally unmeasured address as measured while discarding the
# genuinely measured ones -- silently inverting the exact measured-zero versus
# structural-unmeasurement distinction this layer exists to preserve. The
# mapping was then confirmed empirically: for 2,000 consecutive addresses the
# per-address count of code 1 equals `operators_measured_scalar` in
# FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv in every case. Use
# `load_observation_state_codes` to re-verify against the file rather than
# trusting these names.
STRUCTURALLY_UNMEASURED = 0
MEASURED_SCALAR = 1
COLLISION_UNRESOLVED = 2

AUTHORITY_STATE_NAMES = ("STRUCTURALLY_UNMEASURED", "MEASURED_SCALAR",
                         "MEASURED_COLLISION_UNRESOLVED")


def load_observation_state_codes(state_names: Sequence[str]) -> dict[str, int]:
    """Bind observation-state codes to the authority's own ordering.

    Returns the code for each state name as the authority declares it, and
    refuses a file whose ordering disagrees with the verified mapping instead of
    silently adopting a new one -- a reordered authority changes the meaning of
    every stored byte and must be an explicit decision.
    """
    names = tuple(str(s) for s in state_names)
    if names != AUTHORITY_STATE_NAMES:
        raise AssertionError(
            "STOP_D1_OBSERVATION_STATE_ORDER_DRIFT: authority declares %r but the "
            "verified mapping is %r; refusing to reinterpret stored state bytes"
            % (list(names), list(AUTHORITY_STATE_NAMES)))
    codes = {name: index for index, name in enumerate(names)}
    if codes["MEASURED_SCALAR"] != MEASURED_SCALAR:
        raise AssertionError("STOP_D1_OBSERVATION_STATE_CODE_MISMATCH")
    return codes


class MolecularAssociationAccumulator:
    """Streaming, mask-aware program/address association sufficient statistics.

    Accumulates only over cells where an address is physically measurable. A
    measured zero contributes a real 0.0; a structurally unmeasured address
    contributes nothing at all and its measured mass stays lower. Encoding
    unmeasurement as a biological zero would manufacture a real association from
    a technical absence, which is the specific failure this class exists to
    prevent, so the two are tracked in separate accumulators.
    """

    def __init__(self, programs: int, addresses: int, dtype: Any = np.float64) -> None:
        if int(programs) <= 0 or int(addresses) <= 0:
            raise ValueError("programs and addresses must be positive")
        self.programs = int(programs)
        self.addresses = int(addresses)
        self.dtype = dtype
        shape = (self.programs, self.addresses)
        self.measured_mass = np.zeros(shape, dtype=dtype)      # sum w over measured cells
        self.sum_expression = np.zeros(shape, dtype=dtype)     # sum w x
        self.sum_score = np.zeros(shape, dtype=dtype)          # sum w s
        self.sum_score_expression = np.zeros(shape, dtype=dtype)
        self.sum_score_squared = np.zeros(shape, dtype=dtype)
        self.total_mass = np.zeros(self.addresses, dtype=dtype)  # sum w over ALL cells
        self.unmeasured_mass = np.zeros(self.addresses, dtype=dtype)
        self.rows = 0

    def update(self, *, scores: np.ndarray, expression: np.ndarray,
               observation_state: np.ndarray, weights: np.ndarray) -> "MolecularAssociationAccumulator":
        s = np.asarray(scores, dtype=self.dtype)
        x = np.asarray(expression, dtype=self.dtype)
        state = np.asarray(observation_state)
        w = np.asarray(weights, dtype=self.dtype).reshape(-1)
        n = w.size
        if s.ndim != 2 or s.shape != (n, self.programs):
            raise ValueError("scores must be (n, programs)")
        if x.shape != (n, self.addresses) or state.shape != (n, self.addresses):
            raise ValueError("expression and observation_state must be (n, addresses)")
        if np.any(w < 0):
            raise ValueError("STOP_D1_NEGATIVE_WEIGHT")
        measured = state == MEASURED_SCALAR
        if np.any(~np.isfinite(x[measured])):
            raise ValueError("STOP_D1_NON_FINITE_MEASURED_EXPRESSION")

        wm = w[:, None] * measured                       # (n, addresses)
        self.total_mass += w.sum() * np.ones(self.addresses, dtype=self.dtype)
        self.unmeasured_mass += (w[:, None] * (~measured)).sum(axis=0)
        x_safe = np.where(measured, x, 0.0)
        for p in range(self.programs):
            sp = s[:, p][:, None]
            self.measured_mass[p] += wm.sum(axis=0)
            self.sum_expression[p] += (wm * x_safe).sum(axis=0)
            self.sum_score[p] += (wm * sp).sum(axis=0)
            self.sum_score_expression[p] += (wm * sp * x_safe).sum(axis=0)
            self.sum_score_squared[p] += (wm * sp * sp).sum(axis=0)
        self.rows += int(n)
        return self

    def effects(self) -> dict[str, Any]:
        """Signed weighted regression slope of expression on score, per address.

        The full signed table is the primary output; no thresholded gene list is
        produced here. Addresses with no measured mass are `nan` and flagged
        NOT_ESTIMABLE rather than reported as a zero effect.
        """
        mass = self.measured_mass
        with np.errstate(invalid="ignore", divide="ignore"):
            mean_s = np.where(mass > 0, self.sum_score / mass, np.nan)
            mean_x = np.where(mass > 0, self.sum_expression / mass, np.nan)
            cov_sx = np.where(mass > 0, self.sum_score_expression / mass - mean_s * mean_x, np.nan)
            var_s = np.where(mass > 0, self.sum_score_squared / mass - mean_s * mean_s, np.nan)
            slope = np.where(var_s > 0, cov_sx / var_s, np.nan)
        measured_fraction = np.where(self.total_mass > 0,
                                     mass / np.maximum(self.total_mass, 1e-300), np.nan)
        return {
            "schema": "d1-molecular-association-v1",
            "effect": slope,
            "covariance_score_expression": cov_sx,
            "score_variance": var_s,
            "measured_mass": mass,
            "measured_fraction": measured_fraction,
            "not_estimable": ~(mass > 0) | ~(var_s > 0),
            "measured_zero_is_data": True,
            "unmeasured_encoded_as_zero": False,
            "rows": self.rows,
        }


def program_measurement_support(effects: np.ndarray, measured_fraction: np.ndarray) -> dict[str, Any]:
    """support_p = sum_g |effect| * measured_fraction / sum_g |effect|.

    Reported as a technical-support diagnostic. A program whose support is low
    is not thereby rejected; the dependence is reported explicitly so it is not
    silently read as biology.
    """
    e = np.asarray(effects, dtype=np.float64)
    f = np.asarray(measured_fraction, dtype=np.float64)
    if e.shape != f.shape:
        raise ValueError("effects and measured_fraction must have the same shape")
    finite = np.isfinite(e) & np.isfinite(f)
    out = np.full(e.shape[0], np.nan) if e.ndim == 2 else np.array(np.nan)
    if e.ndim == 1:
        w = np.abs(e[finite])
        return {"support": float((w * f[finite]).sum() / w.sum()) if w.sum() > 0 else float("nan"),
                "statistic_id": "D1-P023:program_measurement_support"}
    for p in range(e.shape[0]):
        m = finite[p]
        w = np.abs(e[p][m])
        out[p] = float((w * f[p][m]).sum() / w.sum()) if w.sum() > 0 else np.nan
    return {"support": out, "statistic_id": "D1-P023:program_measurement_support"}


def technical_sensitivity_view(*, program_scores: np.ndarray,
                               technical_covariate: np.ndarray,
                               weights: np.ndarray, covariate_name: str) -> dict[str, Any]:
    """Falsification view: how strongly does a program track a technical covariate?

    Measurement support, source, operator and sequencing depth are reported
    here as an explicit sensitivity/falsification statistic. This view is
    deliberately not an input to D: using it to select D would let a technical
    artifact define the signal subspace it is supposed to falsify.
    """
    s = np.asarray(program_scores, dtype=np.float64)
    t = np.asarray(technical_covariate, dtype=np.float64).reshape(-1)
    w = np.asarray(weights, dtype=np.float64).reshape(-1)
    if s.ndim == 1:
        s = s[:, None]
    if s.shape[0] != t.size or t.size != w.size:
        raise ValueError("scores, covariate and weights must align")
    mass = float(w.sum())
    mean_t = float((w * t).sum() / mass)
    var_t = float((w * (t - mean_t) ** 2).sum() / mass)
    out = []
    for p in range(s.shape[1]):
        sp = s[:, p]
        mean_s = float((w * sp).sum() / mass)
        var_s = float((w * (sp - mean_s) ** 2).sum() / mass)
        cov = float((w * (sp - mean_s) * (t - mean_t)).sum() / mass)
        denom = math.sqrt(var_s * var_t)
        out.append(float(cov / denom) if denom > 0 else float("nan"))
    return {
        "statistic_id": "D1-SENSITIVITY:technical_dependence",
        "covariate_name": str(covariate_name),
        "weighted_correlation": out,
        "role": "FALSIFICATION_SENSITIVITY_VIEW",
        "used_to_fit_D": False,
        "interpretation": ("a program tracking this covariate must be reported as "
                           "technically dependent, not silently interpreted as biology"),
    }


# ---------------------------------------------------------------------------
# Deterministic catalog ordering, no tuned weights
# ---------------------------------------------------------------------------
def canonical_catalog_order(programs: Sequence[Mapping[str, Any]], *,
                            order_keys: Sequence[str],
                            tie_breaker: str = "program_id") -> dict[str, Any]:
    """Deterministic lexicographic ordering over separate component ranks.

    No weighted composite is formed. Every component rank is published so the
    ordering is inspectable and cannot hide a tuned trade-off.
    """
    rows = list(programs)
    missing = [k for k in list(order_keys) + [tie_breaker]
               if any(k not in r for r in rows)]
    if missing:
        raise ValueError("STOP_D1_CATALOG_ORDER_MISSING_COMPONENT: %r" % sorted(set(missing)))

    def key(row: Mapping[str, Any]) -> tuple:
        # Descending on each component rank, ascending on the tie-breaker.
        return tuple(-float(row[k]) for k in order_keys) + (str(row[tie_breaker]),)

    ordered = sorted(rows, key=key)
    return {"statistic_id": "D1-P027:canonical_program_ranking",
            "order_keys": list(order_keys),
            "tie_breaker": tie_breaker,
            "weighted_composite": None,
            "ordered_program_ids": [str(r[tie_breaker]) for r in ordered],
            "published_component_ranks": [
                {tie_breaker: str(r[tie_breaker]), **{k: float(r[k]) for k in order_keys}}
                for r in ordered],
            }


# ---------------------------------------------------------------------------
# Frozen normalization check
# ---------------------------------------------------------------------------
def assert_frozen_normalization(raw_counts: Sequence[float], source_library: float,
                                observed_log1p: Sequence[float], *,
                                atol: float = 1e-6) -> dict[str, Any]:
    """Verify x = log1p(raw_count * 10000 / full_source_library) exactly once.

    Also round-trips integer counts as round(expm1(x) * L / 10000), matching the
    F1 nuisance formula contract. A double-normalized or differently-scaled
    input fails here rather than silently changing every downstream effect.
    """
    c = np.asarray(raw_counts, dtype=np.float64).reshape(-1)
    x = np.asarray(observed_log1p, dtype=np.float64).reshape(-1)
    L = float(source_library)
    if c.size != x.size:
        raise ValueError("counts and values must align")
    if L <= 0:
        raise ValueError("source_library must be positive")
    expected = np.log1p(c * (10000.0 / L))
    worst = float(np.max(np.abs(expected - x))) if x.size else 0.0
    if worst > atol:
        raise AssertionError("STOP_D1_NORMALIZATION_DRIFT: max |expected-observed| = %.3e" % worst)
    recovered = np.round(np.expm1(x) * L / 10000.0)
    if not np.allclose(recovered, np.round(c), atol=0.5):
        raise AssertionError("STOP_D1_COUNT_ROUNDTRIP_FAILED")
    return {"transform": "log1p(raw_count*10000/full_source_library)",
            "applied_times": 1, "max_deviation": worst,
            "count_roundtrip": "EXACT"}


def canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def payload_root(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def stream_chunks(rows: Sequence[Any], chunk_size: int) -> Iterator[list[Any]]:
    """Chunk an iterable so no stage materialises the full population."""
    if int(chunk_size) <= 0:
        raise ValueError("chunk_size must be positive")
    buffer: list[Any] = []
    for row in rows:
        buffer.append(row)
        if len(buffer) >= int(chunk_size):
            yield buffer
            buffer = []
    if buffer:
        yield buffer


__all__ = [name for name in dir() if not name.startswith("_")]
