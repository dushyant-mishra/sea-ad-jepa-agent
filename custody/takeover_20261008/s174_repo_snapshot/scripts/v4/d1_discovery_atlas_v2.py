#!/usr/bin/env python3
"""D1 discovery atlas V2: outcome-blind post-D mathematical machinery.

This module turns a retained D-dimensional teacher subspace into stable discovery
objects and computes continuous cell/molecular/donor/source/operator summaries.
It deliberately contains no pathology, no confirmatory thresholds, no novelty
reference set, and no weighted catalog composite.

Production I/O is separated from these calculations. The same functions operate
on known-answer fixtures and on full-real streamed sufficient statistics.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from d1_real_data_derivation_core_v1 import (
    MEASURED_SCALAR,
    descriptive_tail_views,
    weighted_quantile,
    within_donor_centered,
)

STOP_OBJECT_INVALID = "STOP_D1_V2_DISCOVERY_OBJECT_INVALID"
STOP_ASSOCIATION_INVALID = "STOP_D1_V2_MOLECULAR_ASSOCIATION_INVALID"
STOP_CATALOG_NOT_ESTIMABLE = "CATALOG_ORDER_NOT_ESTIMABLE"
NOVELTY_UNAVAILABLE = "NOT_MEASURABLE_NO_FROZEN_REFERENCE_SET"


@dataclass(frozen=True)
class DiscoveryObject:
    program_id: str
    block_index: int
    start_rank: int
    end_rank: int
    axis_indices: tuple[int, ...]
    object_type: str
    basis: np.ndarray
    variance: float
    magnitude: float
    stability_margin: float

    @property
    def dimension(self) -> int:
        return len(self.axis_indices)

    def as_dict(self) -> dict[str, Any]:
        return {
            "program_id": self.program_id,
            "block_index": self.block_index,
            "start_rank": self.start_rank,
            "end_rank": self.end_rank,
            "axis_indices": list(self.axis_indices),
            "object_type": self.object_type,
            "dimension": self.dimension,
            "variance": self.variance,
            "magnitude": self.magnitude,
            "stability_margin": self.stability_margin,
        }


def build_discovery_objects(derivation: Mapping[str, Any]) -> list[DiscoveryObject]:
    D = int(derivation.get("D") or 0)
    if D <= 0:
        raise ValueError(f"{STOP_OBJECT_INVALID}: D")
    eigenvalues = np.asarray(derivation["eigenvalues"], dtype=np.float64)
    vectors = np.asarray(derivation["eigenvectors_leading"], dtype=np.float64)
    if vectors.ndim != 2 or vectors.shape[1] != D:
        raise ValueError(
            f"{STOP_OBJECT_INVALID}: leading eigenvectors must be (p,D)")
    blocks = [list(map(int, b)) for b in derivation["degeneracy_blocks"]]
    flattened = [x for b in blocks for x in b]
    if not blocks or flattened != list(range(len(eigenvalues))):
        raise ValueError(
            f"{STOP_OBJECT_INVALID}: degeneracy blocks must be ordered and exactly "
            "partition the spectrum")
    retained = []
    for block_index, block in enumerate(blocks):
        if not block:
            raise ValueError(f"{STOP_OBJECT_INVALID}: empty block")
        expected = list(range(block[0], block[-1] + 1))
        if block != expected:
            raise ValueError(f"{STOP_OBJECT_INVALID}: noncontiguous block {block}")
        if block[0] >= D:
            continue
        if block[-1] >= D:
            raise ValueError(
                f"{STOP_OBJECT_INVALID}: D={D} cuts through block {block}")
        retained.append((block_index, block))
    if sum(len(b) for _, b in retained) != D:
        raise ValueError(f"{STOP_OBJECT_INVALID}: retained blocks do not cover 1..D")

    real_lower = np.asarray(derivation["real_overlap_lower"], dtype=np.float64)
    null_upper = np.asarray(derivation["null_overlap_upper"], dtype=np.float64)
    objects = []
    for block_index, block in retained:
        end_rank = block[-1] + 1
        if end_rank > real_lower.size or end_rank > null_upper.size:
            raise ValueError(
                f"{STOP_OBJECT_INVALID}: missing stability boundary {end_rank}")
        variance = float(np.sum(eigenvalues[block]))
        if not math.isfinite(variance) or variance < 0:
            raise ValueError(f"{STOP_OBJECT_INVALID}: variance")
        basis = vectors[:, block].copy()
        gram = basis.T @ basis
        if not np.allclose(gram, np.eye(len(block)), atol=1e-10, rtol=1e-10):
            raise ValueError(
                f"{STOP_OBJECT_INVALID}: retained eigenvectors are not orthonormal")
        # Do NOT QR the basis here. For an isolated axis QR is free to flip the
        # sign, which would destroy the deterministic global eigenvector sign
        # convention. For a degenerate block the original eigenspace basis is
        # already orthonormal and the downstream norm is rotation-invariant.
        objects.append(DiscoveryObject(
            program_id=f"D1OBJ-B{block_index}-R{block[0]+1}-{block[-1]+1}",
            block_index=block_index,
            start_rank=block[0] + 1,
            end_rank=end_rank,
            axis_indices=tuple(block),
            object_type="ISOLATED_AXIS" if len(block) == 1 else "DEGENERATE_SUBSPACE",
            basis=basis,
            variance=variance,
            magnitude=math.sqrt(variance),
            stability_margin=float(real_lower[end_rank - 1] - null_upper[end_rank - 1]),
        ))
    return objects


def score_object(states: np.ndarray, mean: np.ndarray,
                 obj: DiscoveryObject) -> np.ndarray:
    z = np.asarray(states, dtype=np.float64)
    mu = np.asarray(mean, dtype=np.float64).reshape(-1)
    if z.ndim != 2 or z.shape[1] != mu.size or obj.basis.shape[0] != mu.size:
        raise ValueError(f"{STOP_OBJECT_INVALID}: score shape")
    coordinates = (z - mu) @ obj.basis
    if obj.object_type == "ISOLATED_AXIS":
        return coordinates[:, 0]
    return np.linalg.norm(coordinates, axis=1)


def weighted_percentile_midrank(
    values: Sequence[float], weights: Sequence[float]
) -> np.ndarray:
    """Tie-aware weighted empirical percentile.

    Every equal score receives the same midpoint percentile of the tie group's
    weighted mass. Row order can therefore never change a percentile.
    """
    v = np.asarray(values, dtype=np.float64).reshape(-1)
    w = np.asarray(weights, dtype=np.float64).reshape(-1)
    if v.size == 0 or v.size != w.size:
        raise ValueError(f"{STOP_OBJECT_INVALID}: percentile inputs")
    if not np.all(np.isfinite(v)) or not np.all(np.isfinite(w)):
        raise ValueError(f"{STOP_OBJECT_INVALID}: nonfinite percentile inputs")
    if np.any(w < 0):
        raise ValueError(f"{STOP_OBJECT_INVALID}: negative percentile weight")
    total = float(w.sum())
    if total <= 0:
        raise ValueError(f"{STOP_OBJECT_INVALID}: zero percentile weight mass")
    order = np.argsort(v, kind="stable")
    sorted_v, sorted_w = v[order], w[order]
    out_sorted = np.empty_like(sorted_v)
    cumulative_before = 0.0
    start = 0
    while start < sorted_v.size:
        stop = start + 1
        while stop < sorted_v.size and sorted_v[stop] == sorted_v[start]:
            stop += 1
        mass = float(sorted_w[start:stop].sum())
        midpoint = (cumulative_before + 0.5 * mass) / total
        out_sorted[start:stop] = midpoint
        cumulative_before += mass
        start = stop
    out = np.empty_like(v)
    out[order] = out_sorted
    return out


def cell_ranking_table(
    *,
    cell_ids: Sequence[str],
    donors: Sequence[str],
    sources: Sequence[str],
    operators: Sequence[int],
    scores: Sequence[float],
    weights: Sequence[float],
    obj: DiscoveryObject,
    two_sided_tail_probabilities: Sequence[float],
    operator_measurement_support: Mapping[int, float] | None = None,
) -> list[dict[str, Any]]:
    ids = np.asarray([str(x) for x in cell_ids])
    d = np.asarray([str(x) for x in donors])
    src = np.asarray([str(x) for x in sources])
    op = np.asarray([int(x) for x in operators])
    s = np.asarray(scores, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)
    n = len(ids)
    if not (len(d) == len(src) == len(op) == len(s) == len(w) == n):
        raise ValueError(f"{STOP_OBJECT_INVALID}: cell ranking columns")
    if len(set(ids.tolist())) != n:
        raise ValueError(f"{STOP_OBJECT_INVALID}: duplicate cell identity")
    if not np.all(np.isfinite(s)) or not np.all(np.isfinite(w)):
        raise ValueError(f"{STOP_OBJECT_INVALID}: nonfinite score/weight")
    if np.any(w < 0) or float(w.sum()) <= 0:
        raise ValueError(f"{STOP_OBJECT_INVALID}: invalid score weight")
    centered = within_donor_centered(s, d, w)
    global_pct = weighted_percentile_midrank(s, w)
    within_pct = np.empty(n, dtype=np.float64)
    for donor in np.unique(d):
        take = d == donor
        within_pct[take] = weighted_percentile_midrank(s[take], w[take])
    tails = descriptive_tail_views(s, w, two_sided_tail_probabilities)["views"]
    rows = []
    for i in range(n):
        memberships = {
            name: bool(s[i] <= spec["lower_cutpoint"] or s[i] >= spec["upper_cutpoint"])
            for name, spec in tails.items()
        }
        support = (
            None if operator_measurement_support is None
            else operator_measurement_support.get(int(op[i]))
        )
        rows.append({
            "program_id": obj.program_id,
            "canonical_cell_id": str(ids[i]),
            "donor_id": str(d[i]),
            "source": str(src[i]),
            "operator_index": int(op[i]),
            "raw_score": float(s[i]),
            "donor_primary_weight": float(w[i]),
            "within_donor_centered_score": float(centered[i]),
            "global_weighted_percentile": float(global_pct[i]),
            "within_donor_weighted_percentile": float(within_pct[i]),
            "measurement_support": None if support is None else float(support),
            "stability_margin": float(obj.stability_margin),
            "tail_membership": memberships,
            "claim_status": "DISCOVERY_ONLY",
        })
    return rows


@dataclass
class AssociationStats:
    measured_mass: np.ndarray
    sum_expression: np.ndarray
    sum_score: np.ndarray
    sum_score_expression: np.ndarray
    sum_score_squared: np.ndarray
    total_weight: float
    rows: int

    @classmethod
    def zeros(cls, addresses: int) -> "AssociationStats":
        z = lambda: np.zeros(int(addresses), dtype=np.float64)
        return cls(z(), z(), z(), z(), z(), 0.0, 0)

    def update(
        self, *, score: np.ndarray, expression: np.ndarray,
        observation_state: np.ndarray, weights: np.ndarray,
    ) -> None:
        s = np.asarray(score, dtype=np.float64).reshape(-1)
        x = np.asarray(expression, dtype=np.float64)
        state = np.asarray(observation_state)
        w = np.asarray(weights, dtype=np.float64).reshape(-1)
        if x.ndim != 2 or x.shape[0] != s.size or w.size != s.size:
            raise ValueError(f"{STOP_ASSOCIATION_INVALID}: shape")
        if state.ndim == 1:
            if state.size != x.shape[1]:
                raise ValueError(f"{STOP_ASSOCIATION_INVALID}: state width")
            measured = np.broadcast_to(state == MEASURED_SCALAR, x.shape)
        elif state.shape == x.shape:
            measured = state == MEASURED_SCALAR
        else:
            raise ValueError(f"{STOP_ASSOCIATION_INVALID}: state shape")
        if self.measured_mass.size != x.shape[1]:
            raise ValueError(f"{STOP_ASSOCIATION_INVALID}: address count")
        if np.any(w < 0) or not np.all(np.isfinite(w)) or not np.all(np.isfinite(s)):
            raise ValueError(f"{STOP_ASSOCIATION_INVALID}: score/weight")
        if not np.all(np.isfinite(x[measured])):
            raise ValueError(f"{STOP_ASSOCIATION_INVALID}: measured expression")
        wm = w[:, None] * measured
        safe_x = np.where(measured, x, 0.0)
        self.measured_mass += wm.sum(axis=0)
        self.sum_expression += (wm * safe_x).sum(axis=0)
        self.sum_score += (wm * s[:, None]).sum(axis=0)
        self.sum_score_expression += (wm * s[:, None] * safe_x).sum(axis=0)
        self.sum_score_squared += (wm * (s[:, None] ** 2)).sum(axis=0)
        self.total_weight += float(w.sum())
        self.rows += int(s.size)

    def add(self, other: "AssociationStats") -> "AssociationStats":
        if self.measured_mass.shape != other.measured_mass.shape:
            raise ValueError(f"{STOP_ASSOCIATION_INVALID}: stats width")
        return AssociationStats(
            measured_mass=self.measured_mass + other.measured_mass,
            sum_expression=self.sum_expression + other.sum_expression,
            sum_score=self.sum_score + other.sum_score,
            sum_score_expression=self.sum_score_expression + other.sum_score_expression,
            sum_score_squared=self.sum_score_squared + other.sum_score_squared,
            total_weight=self.total_weight + other.total_weight,
            rows=self.rows + other.rows,
        )

    def scaled_sum(self, counts: Sequence[int], banks: Sequence["AssociationStats"]) -> "AssociationStats":
        if len(counts) != len(banks):
            raise ValueError(f"{STOP_ASSOCIATION_INVALID}: bootstrap bank")
        out = AssociationStats.zeros(self.measured_mass.size)
        for count, bank in zip(counts, banks):
            k = int(count)
            if k <= 0:
                continue
            out.measured_mass += k * bank.measured_mass
            out.sum_expression += k * bank.sum_expression
            out.sum_score += k * bank.sum_score
            out.sum_score_expression += k * bank.sum_score_expression
            out.sum_score_squared += k * bank.sum_score_squared
            out.total_weight += k * bank.total_weight
            out.rows += k * bank.rows
        return out

    def effects(self) -> dict[str, np.ndarray]:
        mass = self.measured_mass
        with np.errstate(divide="ignore", invalid="ignore"):
            mean_s = np.where(mass > 0, self.sum_score / mass, np.nan)
            mean_x = np.where(mass > 0, self.sum_expression / mass, np.nan)
            cov = np.where(
                mass > 0,
                self.sum_score_expression / mass - mean_s * mean_x,
                np.nan,
            )
            var_s = np.where(
                mass > 0,
                self.sum_score_squared / mass - mean_s * mean_s,
                np.nan,
            )
            effect = np.where(var_s > 0, cov / var_s, np.nan)
            measured_fraction = np.where(
                self.total_weight > 0,
                mass / self.total_weight,
                np.nan,
            )
        return {
            "effect": effect,
            "measured_fraction": measured_fraction,
            "score_variance": var_s,
            "not_estimable": ~(mass > 0) | ~(var_s > 0),
        }


class GroupedAssociationAccumulator:
    """One-object grouped sufficient statistics.

    Groups are global, donor, source and operator. The caller processes objects
    one at a time, keeping memory bounded by groups x addresses rather than
    cells x addresses.
    """

    def __init__(self, addresses: int) -> None:
        self.addresses = int(addresses)
        self.groups: dict[tuple[str, str], AssociationStats] = {}

    def _get(self, kind: str, key: Any) -> AssociationStats:
        token = (str(kind), str(key))
        if token not in self.groups:
            self.groups[token] = AssociationStats.zeros(self.addresses)
        return self.groups[token]

    def update(
        self, *, donor: str, source: str, operator: int,
        score: np.ndarray, expression: np.ndarray,
        observation_state: np.ndarray, weights: np.ndarray,
    ) -> None:
        for kind, key in (
            ("global", "ALL"),
            ("donor", donor),
            ("source", source),
            ("operator", int(operator)),
        ):
            self._get(kind, key).update(
                score=score, expression=expression,
                observation_state=observation_state, weights=weights)

    def group_effects(self, kind: str) -> dict[str, dict[str, np.ndarray]]:
        return {
            key: stats.effects()
            for (group_kind, key), stats in sorted(self.groups.items())
            if group_kind == kind
        }

    def global_effects(self) -> dict[str, np.ndarray]:
        return self.groups[("global", "ALL")].effects()


def _finite_cosine_diagnostic(a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
    x = np.asarray(a, dtype=np.float64)
    y = np.asarray(b, dtype=np.float64)
    finite = np.isfinite(x) & np.isfinite(y)
    common = int(np.sum(finite))
    if common == 0:
        return {"cosine": None, "common_finite_addresses": 0}
    xx, yy = x[finite], y[finite]
    nx, ny = float(np.linalg.norm(xx)), float(np.linalg.norm(yy))
    if nx <= 0 or ny <= 0:
        return {"cosine": None, "common_finite_addresses": common}
    return {
        "cosine": float(np.dot(xx, yy) / (nx * ny)),
        "common_finite_addresses": common,
    }


def donor_recurrence_summary(
    global_effect: np.ndarray,
    donor_effects: Mapping[str, Mapping[str, np.ndarray]],
) -> dict[str, Any]:
    diagnostics = {}
    cosines = {}
    for donor, payload in donor_effects.items():
        diag = _finite_cosine_diagnostic(payload["effect"], global_effect)
        diagnostics[str(donor)] = diag
        if diag["cosine"] is not None:
            cosines[str(donor)] = float(diag["cosine"])
    values = list(cosines.values())
    if not values:
        return {
            "estimable": False,
            "donor_recurrence": None,
            "cosines": {},
            "positive_fraction": None,
            "estimable_donors": 0,
            "donor_diagnostics": diagnostics,
        }
    return {
        "estimable": True,
        "donor_recurrence": float(np.median(values)),
        "cosines": cosines,
        "positive_fraction": float(np.mean(np.asarray(values) > 0)),
        "estimable_donors": len(values),
        "donor_diagnostics": diagnostics,
    }


def source_operator_consistency_summary(
    global_effect: np.ndarray,
    source_effects: Mapping[str, Mapping[str, np.ndarray]],
    operator_effects: Mapping[str, Mapping[str, np.ndarray]],
) -> dict[str, Any]:
    def collect(groups):
        out, diagnostics = {}, {}
        for key, payload in groups.items():
            diag = _finite_cosine_diagnostic(payload["effect"], global_effect)
            diagnostics[str(key)] = diag
            if diag["cosine"] is not None:
                out[str(key)] = float(diag["cosine"])
        return out, diagnostics

    source, source_diagnostics = collect(source_effects)
    operator, operator_diagnostics = collect(operator_effects)
    if not source or not operator:
        return {
            "estimable": False,
            "source_operator_consistency": None,
            "source_cosines": source,
            "operator_cosines": operator,
            "source_diagnostics": source_diagnostics,
            "operator_diagnostics": operator_diagnostics,
        }
    source_median = float(np.median(list(source.values())))
    operator_median = float(np.median(list(operator.values())))
    return {
        "estimable": True,
        "source_consistency": source_median,
        "operator_consistency": operator_median,
        "source_operator_consistency": min(source_median, operator_median),
        "source_cosines": source,
        "operator_cosines": operator,
        "source_diagnostics": source_diagnostics,
        "operator_diagnostics": operator_diagnostics,
    }


def measurement_support(effect: np.ndarray, measured_fraction: np.ndarray) -> float | None:
    e = np.asarray(effect, dtype=np.float64)
    f = np.asarray(measured_fraction, dtype=np.float64)
    finite = np.isfinite(e) & np.isfinite(f)
    magnitude = np.abs(e[finite])
    denom = float(magnitude.sum())
    if denom <= 0:
        return None
    return float(np.sum(magnitude * f[finite]) / denom)


def molecular_concentration(effect: np.ndarray) -> dict[str, float | None]:
    e = np.asarray(effect, dtype=np.float64)
    magnitude = np.abs(e[np.isfinite(e)])
    total = float(magnitude.sum())
    if total <= 0:
        return {"molecular_concentration": None,
                "molecular_effective_address_count": None}
    p = magnitude / total
    concentration = float(np.sum(p * p))
    return {
        "molecular_concentration": concentration,
        "molecular_effective_address_count": float(1.0 / concentration),
    }


def operator_measurement_support(
    effect: np.ndarray, operator_observation_state: np.ndarray
) -> dict[int, float | None]:
    e = np.asarray(effect, dtype=np.float64)
    state = np.asarray(operator_observation_state)
    if state.ndim != 2 or state.shape[1] != e.size:
        raise ValueError(f"{STOP_ASSOCIATION_INVALID}: operator state shape")
    magnitude = np.abs(e)
    finite = np.isfinite(magnitude)
    denom = float(magnitude[finite].sum())
    out = {}
    for operator in range(state.shape[0]):
        if denom <= 0:
            out[operator] = None
            continue
        measured = (state[operator] == MEASURED_SCALAR) & finite
        out[operator] = float(magnitude[measured].sum() / denom)
    return out


def bootstrap_effect_block(
    donor_stats: Sequence[AssociationStats], *, bootstrap_counts: np.ndarray,
    address_slice: slice,
) -> np.ndarray:
    """Exact donor-block bootstrap effects for one address block.

    bootstrap_counts is (R, donors), containing donor multiplicities. Processing
    addresses in blocks avoids an R x 41,238 x all-statistics dense object.
    """
    counts = np.asarray(bootstrap_counts, dtype=np.int64)
    if counts.ndim != 2 or counts.shape[1] != len(donor_stats):
        raise ValueError(f"{STOP_ASSOCIATION_INVALID}: bootstrap counts")
    sl = address_slice
    fields = (
        "measured_mass", "sum_expression", "sum_score",
        "sum_score_expression", "sum_score_squared",
    )
    matrices = {
        field: np.stack([getattr(s, field)[sl] for s in donor_stats], axis=0)
        for field in fields
    }
    mass = counts @ matrices["measured_mass"]
    sum_x = counts @ matrices["sum_expression"]
    sum_s = counts @ matrices["sum_score"]
    sum_sx = counts @ matrices["sum_score_expression"]
    sum_s2 = counts @ matrices["sum_score_squared"]
    with np.errstate(divide="ignore", invalid="ignore"):
        mean_s = np.where(mass > 0, sum_s / mass, np.nan)
        mean_x = np.where(mass > 0, sum_x / mass, np.nan)
        cov = np.where(mass > 0, sum_sx / mass - mean_s * mean_x, np.nan)
        var_s = np.where(mass > 0, sum_s2 / mass - mean_s * mean_s, np.nan)
        effect = np.where(var_s > 0, cov / var_s, np.nan)
    return effect


def catalog_components(
    *, obj: DiscoveryObject, global_effects: Mapping[str, np.ndarray],
    donor_summary: Mapping[str, Any], consistency_summary: Mapping[str, Any],
) -> dict[str, Any]:
    support = measurement_support(
        global_effects["effect"], global_effects["measured_fraction"])
    concentration = molecular_concentration(global_effects["effect"])
    return {
        "program_id": obj.program_id,
        "stability_margin": float(obj.stability_margin),
        "donor_recurrence": donor_summary.get("donor_recurrence"),
        "magnitude": float(obj.magnitude),
        "source_operator_consistency": consistency_summary.get(
            "source_operator_consistency"),
        "measurement_support": support,
        "molecular_concentration": concentration["molecular_concentration"],
        "molecular_effective_address_count":
            concentration["molecular_effective_address_count"],
        "novelty": NOVELTY_UNAVAILABLE,
        "claim_status": "DISCOVERY_ONLY",
    }


CATALOG_KEYS = (
    "stability_margin", "donor_recurrence", "magnitude",
    "source_operator_consistency", "measurement_support",
    "molecular_concentration",
)


def order_catalog(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    estimable, not_estimable = [], []
    for row in rows:
        if all(row.get(key) is not None and math.isfinite(float(row[key]))
               for key in CATALOG_KEYS):
            estimable.append(dict(row))
        else:
            item = dict(row)
            item["catalog_order_status"] = STOP_CATALOG_NOT_ESTIMABLE
            not_estimable.append(item)

    def key(row: Mapping[str, Any]) -> tuple[Any, ...]:
        return tuple(-float(row[k]) for k in CATALOG_KEYS) + (str(row["program_id"]),)

    ordered = sorted(estimable, key=key)
    for index, row in enumerate(ordered, start=1):
        row["catalog_rank"] = index
        row["catalog_order_status"] = "ESTIMABLE"
    return {
        "ordered_estimable": ordered,
        "not_estimable": sorted(not_estimable, key=lambda r: str(r["program_id"])),
        "order_keys": list(CATALOG_KEYS),
        "weighted_composite": None,
        "novelty_used_in_primary_order": False,
    }


def representative_cells(
    rows: Sequence[Mapping[str, Any]], *, each_tail: int
) -> dict[str, list[dict[str, Any]]]:
    """Descriptive exemplars only; count must come from frozen procedure config."""
    n = int(each_tail)
    if n < 0:
        raise ValueError(f"{STOP_OBJECT_INVALID}: negative exemplar count")
    ordered = sorted(
        rows, key=lambda r: (float(r["raw_score"]), str(r["canonical_cell_id"])))
    return {
        "lowest": [dict(r) for r in ordered[:n]],
        "highest": [dict(r) for r in ordered[-n:][::-1]] if n else [],
        "selection_role": "DESCRIPTIVE_EXEMPLARS_ONLY",
    }


def representative_donors(
    rows: Sequence[Mapping[str, Any]], *, each_tail: int
) -> dict[str, list[dict[str, Any]]]:
    """Donor summaries use the same donor-primary cell weights as D1."""
    n = int(each_tail)
    if n < 0:
        raise ValueError(f"{STOP_OBJECT_INVALID}: negative exemplar count")
    by_donor: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        by_donor.setdefault(str(row["donor_id"]), []).append(row)
    summaries = []
    for donor, donor_rows in by_donor.items():
        scores = np.asarray([float(r["raw_score"]) for r in donor_rows], dtype=np.float64)
        weights = np.asarray(
            [float(r["donor_primary_weight"]) for r in donor_rows], dtype=np.float64)
        if np.any(weights < 0) or float(weights.sum()) <= 0:
            raise ValueError(f"{STOP_OBJECT_INVALID}: donor exemplar weights")
        weighted_mean = float(np.sum(scores * weights) / np.sum(weights))
        weighted_median = float(weighted_quantile(scores, weights, [0.5])[0])
        summaries.append({
            "donor_id": donor,
            "weighted_mean_score": weighted_mean,
            "weighted_median_score": weighted_median,
            "cells": len(scores),
        })
    summaries.sort(key=lambda r: (r["weighted_mean_score"], r["donor_id"]))
    return {
        "lowest": summaries[:n],
        "highest": summaries[-n:][::-1] if n else [],
        "selection_role": "DESCRIPTIVE_EXEMPLARS_ONLY",
    }
