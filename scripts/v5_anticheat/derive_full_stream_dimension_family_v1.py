#!/usr/bin/env python3
"""Dataset-first dimension-family adjudication for V5.

This module implements only prospectively frozen rank-selection mechanics. It
never fabricates FULL104 metrics and never authorizes training. The production
metric executor must separately compute its inputs from the authenticated full
reader-fit stream with full-refit matched nulls and precision-derived replicate
counts.
"""
from __future__ import annotations

import math
from typing import Mapping, Sequence

_SHARED_FLAGS = (
    "signal_above_full_refit_matched_null",
    "donor_resampled_subspace_stability",
    "held_donor_cross_view_predictability",
    "independent_view_agreement",
    "measurement_shortcut_increment_pass",
)
_PRIVATE_FLAGS = (
    "held_donor_increment_pass",
    "held_operator_increment_pass",
    "measurement_shortcut_increment_pass",
    "same_cell_technical_intervention_stability_pass",
)


def _finite_float(value: object, name: str, *, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{name} must be finite")
    if nonnegative and out < 0:
        raise ValueError(f"{name} must be nonnegative")
    return out


def _normalize_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    mean_key: str,
    se_key: str,
    flags: tuple[str, ...],
) -> list[dict[str, object]]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise ValueError("dimension rows must be a nonempty sequence")
    out: list[dict[str, object]] = []
    for expected_rank, row in enumerate(rows, start=1):
        if not isinstance(row, Mapping):
            raise ValueError("dimension rows must be mappings")
        rank = row.get("rank")
        if isinstance(rank, bool) or not isinstance(rank, int) or rank != expected_rank:
            raise ValueError("rank rows must be consecutive positive integers starting at 1")
        mean = _finite_float(row.get(mean_key), mean_key)
        se = _finite_float(row.get(se_key), se_key, nonnegative=True)
        support_values = []
        for flag in flags:
            value = row.get(flag)
            if value not in (True, False):
                raise ValueError(f"{flag} must be explicit boolean")
            support_values.append(value is True)
        out.append({
            "rank": rank,
            "mean": mean,
            "se": se,
            "jointly_supported": all(support_values),
        })
    return out


def _normalize_score_rows(
    rows: Sequence[Mapping[str, object]], *, mean_key: str, se_key: str
) -> list[dict[str, float | int]]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise ValueError("dimension rows must be a nonempty sequence")
    out: list[dict[str, float | int]] = []
    for expected_rank, row in enumerate(rows, start=1):
        if not isinstance(row, Mapping):
            raise ValueError("dimension rows must be mappings")
        rank = row.get("rank")
        if isinstance(rank, bool) or not isinstance(rank, int) or rank != expected_rank:
            raise ValueError("rank rows must be consecutive positive integers starting at 1")
        out.append({
            "rank": rank,
            "mean": _finite_float(row.get(mean_key), mean_key),
            "se": _finite_float(row.get(se_key), se_key, nonnegative=True),
        })
    return out


def _select_contiguous_one_se(
    rows: Sequence[Mapping[str, object]],
    *,
    mean_key: str,
    se_key: str,
    flags: tuple[str, ...],
    dimension_name: str,
    pass_terminal: str,
    expand_terminal: str,
) -> dict[str, object]:
    normalized = _normalize_rows(rows, mean_key=mean_key, se_key=se_key, flags=flags)
    contiguous = 0
    for row in normalized:
        if row["jointly_supported"]:
            contiguous += 1
        else:
            break

    boundary_supported = contiguous == len(normalized)
    if boundary_supported:
        return {
            "terminal": expand_terminal,
            dimension_name: None,
            "contiguous_prefix_supported_through": contiguous,
            "search_boundary_supported": True,
            "one_se_threshold": None,
            "training_authorized": False,
        }

    if contiguous == 0:
        return {
            "terminal": pass_terminal,
            dimension_name: 0,
            "contiguous_prefix_supported_through": 0,
            "search_boundary_supported": False,
            "one_se_threshold": None,
            "training_authorized": False,
        }

    eligible = normalized[:contiguous]
    best = max(eligible, key=lambda row: row["mean"])
    threshold = float(best["mean"]) - float(best["se"])
    selected = next(int(row["rank"]) for row in eligible if float(row["mean"]) >= threshold)
    return {
        "terminal": pass_terminal,
        dimension_name: selected,
        "contiguous_prefix_supported_through": contiguous,
        "search_boundary_supported": False,
        "best_supported_rank": int(best["rank"]),
        "best_supported_mean": float(best["mean"]),
        "best_supported_se": float(best["se"]),
        "one_se_threshold": threshold,
        "training_authorized": False,
    }


def select_shared_dimension(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Apply the frozen shared-rank joint-support + one-SE prefix rule."""
    return _select_contiguous_one_se(
        rows,
        mean_key="held_donor_cross_view_mean",
        se_key="held_donor_cross_view_se",
        flags=_SHARED_FLAGS,
        dimension_name="D_shared",
        pass_terminal="PASS_D_SHARED_SELECTED",
        expand_terminal="EXPAND_SHARED_SEARCH_ENVELOPE",
    )


def select_private_dimension(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Apply prospective D_private candidate V1 after D_shared is frozen."""
    return _select_contiguous_one_se(
        rows,
        mean_key="held_donor_increment_mean",
        se_key="held_donor_increment_se",
        flags=_PRIVATE_FLAGS,
        dimension_name="D_private",
        pass_terminal="PASS_D_PRIVATE_SELECTED",
        expand_terminal="EXPAND_PRIVATE_SEARCH_ENVELOPE",
    )


def select_observation_dimension(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Apply prospective D_obs candidate V1 using held-operator reconstruction."""
    normalized = _normalize_score_rows(
        rows,
        mean_key="held_operator_reconstruction_mean",
        se_key="held_operator_reconstruction_se",
    )
    best_mean = max(float(row["mean"]) for row in normalized)
    boundary = normalized[-1]
    if float(boundary["mean"]) == best_mean:
        return {
            "terminal": "EXPAND_OBSERVATION_SEARCH_ENVELOPE",
            "D_obs": None,
            "best_rank": int(boundary["rank"]),
            "search_boundary_best": True,
            "one_se_threshold": None,
            "training_authorized": False,
        }
    best = next(row for row in normalized if float(row["mean"]) == best_mean)
    threshold = float(best["mean"]) - float(best["se"])
    selected = next(int(row["rank"]) for row in normalized if float(row["mean"]) >= threshold)
    return {
        "terminal": "PASS_D_OBS_SELECTED",
        "D_obs": selected,
        "best_rank": int(best["rank"]),
        "best_mean": float(best["mean"]),
        "best_se": float(best["se"]),
        "one_se_threshold": threshold,
        "search_boundary_best": False,
        "training_authorized": False,
    }
