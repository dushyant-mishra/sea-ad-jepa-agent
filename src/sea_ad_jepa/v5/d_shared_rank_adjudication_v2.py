from __future__ import annotations

import math
from typing import Mapping, Sequence


_FLAGS = (
    "signal_above_full_refit_matched_null",
    "donor_resampled_subspace_stability",
    "held_donor_cross_view_predictability",
    "independent_view_agreement",
    "measurement_shortcut_increment_pass",
)


def _number(value: object, field: str, *, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{field} must be finite")
    if nonnegative and out < 0:
        raise ValueError(f"{field} must be nonnegative")
    return out


def _normalize(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise ValueError("D_shared rows must be a nonempty sequence")
    if len(rows) > 512:
        raise ValueError("D_shared V2 permits at most 512 rank rows")
    out: list[dict[str, object]] = []
    for expected_rank, row in enumerate(rows, start=1):
        if not isinstance(row, Mapping):
            raise ValueError("D_shared rows must be mappings")
        rank = row.get("rank")
        if isinstance(rank, bool) or not isinstance(rank, int) or rank != expected_rank:
            raise ValueError("rank rows must be consecutive positive integers starting at 1")
        support: list[bool] = []
        for flag in _FLAGS:
            value = row.get(flag)
            if value not in (True, False):
                raise ValueError(f"{flag} must be explicit boolean")
            support.append(value is True)
        out.append({
            "rank": rank,
            "mean": _number(row.get("held_donor_cross_view_mean"), "held_donor_cross_view_mean"),
            "se": _number(row.get("held_donor_cross_view_se"), "held_donor_cross_view_se", nonnegative=True),
            "jointly_supported": all(support),
        })
    return out


def _one_se_select(rows: Sequence[Mapping[str, object]]) -> tuple[int, dict[str, object], float]:
    best = max(rows, key=lambda row: float(row["mean"]))
    threshold = float(best["mean"]) - float(best["se"])
    selected = next(int(row["rank"]) for row in rows if float(row["mean"]) >= threshold)
    return selected, dict(best), threshold


def select_shared_dimension_v2(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Prospective D_shared V2 contiguous-support + one-SE adjudication over ranks 1..512."""
    normalized = _normalize(rows)
    contiguous = 0
    for row in normalized:
        if row["jointly_supported"]:
            contiguous += 1
        else:
            break

    if contiguous == 0:
        return {
            "terminal": "PASS_D_SHARED_SELECTED_V2",
            "D_shared": 0,
            "contiguous_prefix_supported_through": 0,
            "search_boundary_supported": False,
            "rank_envelope_exhausted": False,
            "one_se_threshold": None,
            "training_authorized": False,
        }

    all_tested_supported = contiguous == len(normalized)
    if all_tested_supported and len(normalized) < 512:
        return {
            "terminal": "EXPAND_SHARED_SEARCH_ENVELOPE_V2",
            "D_shared": None,
            "contiguous_prefix_supported_through": contiguous,
            "search_boundary_supported": True,
            "rank_envelope_exhausted": False,
            "one_se_threshold": None,
            "training_authorized": False,
        }

    eligible = normalized[:contiguous]
    selected, best, threshold = _one_se_select(eligible)
    if all_tested_supported and len(normalized) == 512:
        terminal = "PASS_D_SHARED_FULL_RANK_ENVELOPE_EXHAUSTED"
        boundary_supported = True
        exhausted = True
    else:
        terminal = "PASS_D_SHARED_SELECTED_V2"
        boundary_supported = False
        exhausted = False
    return {
        "terminal": terminal,
        "D_shared": selected,
        "contiguous_prefix_supported_through": contiguous,
        "search_boundary_supported": boundary_supported,
        "rank_envelope_exhausted": exhausted,
        "best_supported_rank": int(best["rank"]),
        "best_supported_mean": float(best["mean"]),
        "best_supported_se": float(best["se"]),
        "one_se_threshold": threshold,
        "training_authorized": False,
    }
