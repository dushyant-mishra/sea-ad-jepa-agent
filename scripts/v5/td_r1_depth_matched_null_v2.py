"""R1 depth-matched null known-truth qualification and executor-boundary repair.

This module repairs the concrete hostile-review failures in the R1 stress lane
without opening human candidate outcomes. It qualifies a donor-preserving
within-depth permutation null on synthetic known-truth worlds and freezes view,
tie, support and source semantics. It does not authorize human R1 PASS/FAIL.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np

from scripts.v5 import td_r1_known_truth_stress_v1 as V1


class R1DepthMatchedNullError(ValueError):
    pass


FAMILY_ALPHA = 0.01
DEPTH_BINS = 5
NULL_DRAWS = 999
NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def null_contract() -> dict:
    return {
        "schema": "JEPA_TD_R1_DEPTH_MATCHED_NULL_CONTRACT_V2",
        "null_semantics": "WITHIN_DONOR_DEPTH_BLOCK_PERMUTATION",
        "depth_block_rule": "FROZEN_QUANTILE_BINS",
        "depth_bin_count": DEPTH_BINS,
        "detection_block_rule": "DESCRIPTIVE_ONLY__NOT_YET_QUALIFIED_FOR_NULL_MATCHING",
        "source_operator_support_preserved": True,
        "view_rule_digest_required": True,
        "eligibility_rule_digest_required": True,
        "tie_tolerance": 0.0,
        "tie_semantics": "EXACT_DISTANCE_TIE_RETAINED_AS_ZERO",
        "both_tie_is_informative_agreement": False,
        "null_draws": NULL_DRAWS,
        "alpha": FAMILY_ALPHA,
        "human_r1_adjudication_authorized": False,
        "authority": dict(NO_AUTHORITY),
    }


def _pair(value, label: str) -> tuple[int, int]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) != 2:
        raise R1DepthMatchedNullError(f"{label} must be a two-address pair")
    a, b = value
    if isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, int) or not isinstance(b, int):
        raise R1DepthMatchedNullError(f"{label} addresses must be integers")
    if a < 0 or b < 0 or a == b:
        raise R1DepthMatchedNullError(f"{label} addresses must be distinct nonnegative integers")
    return int(a), int(b)


def validate_view_pairs(view_x, view_y) -> dict:
    if isinstance(view_x, (str, bytes)) or not isinstance(view_x, Sequence) or not view_x:
        raise R1DepthMatchedNullError("view_x must be a nonempty sequence")
    if isinstance(view_y, (str, bytes)) or not isinstance(view_y, Sequence) or not view_y:
        raise R1DepthMatchedNullError("view_y must be a nonempty sequence")
    x = [_pair(v, "view_x pair") for v in view_x]
    y = [_pair(v, "view_y pair") for v in view_y]

    def canonical(p):
        return tuple(sorted(p))

    xc = [canonical(p) for p in x]
    yc = [canonical(p) for p in y]
    if len(set(xc)) != len(xc) or len(set(yc)) != len(yc):
        raise R1DepthMatchedNullError("duplicate or reversed molecular pairs are forbidden")
    x_addresses = {v for p in x for v in p}
    y_addresses = {v for p in y for v in p}
    if len(x_addresses) != 2 * len(x) or len(y_addresses) != 2 * len(y):
        raise R1DepthMatchedNullError("duplicate address use within a molecular view is forbidden")
    if x_addresses & y_addresses:
        raise R1DepthMatchedNullError("molecular views must be address-disjoint")
    return {
        "view_x_pairs": len(x),
        "view_y_pairs": len(y),
        "view_x_addresses": len(x_addresses),
        "view_y_addresses": len(y_addresses),
        "views_disjoint": True,
    }


def summarize_source_recurrence(rows, *, required_sources) -> dict:
    if isinstance(required_sources, (str, bytes)) or not isinstance(required_sources, Sequence) or not required_sources:
        raise R1DepthMatchedNullError("required_sources must be a nonempty sequence")
    sources = []
    for value in required_sources:
        if not isinstance(value, str) or not value:
            raise R1DepthMatchedNullError("required source must be a nonempty string")
        sources.append(value)
    if len(set(sources)) != len(sources):
        raise R1DepthMatchedNullError("required_sources must be unique")
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise R1DepthMatchedNullError("rows must be a sequence")

    seen_donor_source: dict[str, str] = {}
    normalized = []
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping) or set(raw) != {"donor_id", "source", "status", "delta"}:
            raise R1DepthMatchedNullError(f"rows[{index}] fields differ from frozen schema")
        donor = raw["donor_id"]
        source = raw["source"]
        status = raw["status"]
        if not isinstance(donor, str) or not donor or not isinstance(source, str) or not source:
            raise R1DepthMatchedNullError("donor/source must be nonempty strings")
        if source not in sources:
            raise R1DepthMatchedNullError(f"row source outside required envelope: {source}")
        previous = seen_donor_source.get(donor)
        if previous is not None and previous != source:
            raise R1DepthMatchedNullError("donor may not be pooled across source identities")
        if previous is not None:
            raise R1DepthMatchedNullError("duplicate donor/source row")
        seen_donor_source[donor] = source
        if status not in {"SUPPORTED", "UNSUPPORTED"}:
            raise R1DepthMatchedNullError("status must be SUPPORTED or UNSUPPORTED")
        if status == "SUPPORTED":
            value = raw["delta"]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise R1DepthMatchedNullError("supported delta must be finite numeric")
            delta = float(value)
        else:
            if raw["delta"] is not None:
                raise R1DepthMatchedNullError("unsupported donor may not carry fake delta")
            delta = None
        normalized.append({"donor_id": donor, "source": source, "status": status, "delta": delta})

    source_status = {}
    source_details = {}
    for source in sources:
        local = [r for r in normalized if r["source"] == source]
        supported = [r for r in local if r["status"] == "SUPPORTED"]
        unsupported = [r for r in local if r["status"] == "UNSUPPORTED"]
        if not local or unsupported or not supported:
            status = "NOT_ESTIMABLE"
        else:
            # Diagnostic only: all supported donor rows retained; no biological
            # threshold or human PASS/FAIL authority is created here.
            status = "DIAGNOSTIC_ONLY"
        source_status[source] = status
        source_details[source] = {
            "total_donor_count": len(local),
            "supported_donor_count": len(supported),
            "unsupported_donor_count": len(unsupported),
            "supported_deltas": [r["delta"] for r in supported],
        }
    overall = "NOT_ESTIMABLE" if any(v == "NOT_ESTIMABLE" for v in source_status.values()) else "DIAGNOSTIC_ONLY"
    return {
        "schema": "JEPA_TD_R1_SOURCE_RECURRENCE_SUMMARY_V2",
        "overall_status": overall,
        "source_status": source_status,
        "source_details": source_details,
        "noncompensating_across_required_sources": True,
        "human_r1_adjudication_authorized": False,
        "authority": dict(NO_AUTHORITY),
    }


def _world(rng: np.random.Generator, n_cells: int, n_genes: int, depth_sd: float, bio: float) -> np.ndarray:
    base = rng.lognormal(-1.0, 1.0, size=n_genes)
    depth = np.exp(rng.normal(0.0, depth_sd, size=n_cells))
    lam = np.outer(depth, base)
    if bio > 0:
        lam = lam * np.exp(bio * rng.normal(size=(n_cells, 1)) @ rng.normal(size=(1, n_genes)))
    return rng.poisson(lam)


def _signs(X: np.ndarray, addresses: np.ndarray) -> np.ndarray:
    return np.sign(X[:, addresses[0::2]] - X[:, addresses[1::2]])


def _distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(np.abs(a - b)) / 2.0)


def _order(a: float, b: float) -> int:
    if a > b:
        return 1
    if a < b:
        return -1
    return 0


def _run_known_truth_world(rng: np.random.Generator, *, depth_sd: float, bio: float,
                           n_donors: int = 8, n_cells: int = 120, n_genes: int = 400,
                           n_triplets: int = 600) -> dict:
    per_donor = {}
    donors_defeating = 0
    for dn in range(n_donors):
        X = _world(rng, n_cells, n_genes, depth_sd, bio)
        library = X.sum(axis=1)
        cut = np.quantile(library, np.linspace(0.0, 1.0, DEPTH_BINS + 1)[1:-1])
        depth_bin = np.searchsorted(cut, library)
        sx = _signs(X, np.arange(0, n_genes // 2))
        sy = _signs(X, np.arange(n_genes // 2, n_genes))
        qx, qy, blocks = [], [], []
        seen = set()
        while len(qx) < n_triplets:
            i, j, k = rng.choice(n_cells, 3, replace=False)
            j, k = sorted((int(j), int(k)))
            i = int(i)
            key = (i, j, k)
            if key in seen:
                continue
            seen.add(key)
            qx.append(_order(_distance(sx[i], sx[j]), _distance(sx[i], sx[k])))
            qy.append(_order(_distance(sy[i], sy[j]), _distance(sy[i], sy[k])))
            blocks.append((int(depth_bin[i]), int(depth_bin[j]), int(depth_bin[k])))
        qx = np.asarray(qx, dtype=int)
        qy = np.asarray(qy, dtype=int)
        informative = ~((qx == 0) & (qy == 0))
        if not informative.any():
            per_donor[f"D{dn}"] = None
            continue
        observed = float(np.mean(qx[informative] == qy[informative]))
        groups: dict[tuple[int, int, int], list[int]] = {}
        for idx, block in enumerate(blocks):
            groups.setdefault(block, []).append(idx)
        null_stats = np.empty(NULL_DRAWS, dtype=float)
        for draw in range(NULL_DRAWS):
            perm = np.arange(n_triplets)
            for group in groups.values():
                ids = np.asarray(group, dtype=int)
                perm[ids] = rng.permutation(ids)
            permuted = qy[perm]
            informative_null = ~((qx == 0) & (permuted == 0))
            null_stats[draw] = float(np.mean(qx[informative_null] == permuted[informative_null]))
        rank = int(math.ceil((NULL_DRAWS + 1) * (1.0 - FAMILY_ALPHA)))
        null_q99 = float(np.sort(null_stats)[rank - 1])
        delta = observed - null_q99
        donors_defeating += int(delta > 0.0)
        per_donor[f"D{dn}"] = delta
    values = [v for v in per_donor.values() if v is not None]
    return {
        "donors_defeating_null": donors_defeating,
        "donor_count": n_donors,
        "mean_delta": float(np.mean(values)) if values else None,
        "per_donor_delta": per_donor,
    }


def qualify_depth_matched_r1_null(*, seed: int = 777) -> dict:
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise R1DepthMatchedNullError("seed must be a nonnegative integer")
    rng = np.random.default_rng(seed)
    technical = _run_known_truth_world(rng, depth_sd=1.0, bio=0.0)
    clean = _run_known_truth_world(rng, depth_sd=0.0, bio=0.0)
    planted = _run_known_truth_world(rng, depth_sd=0.0, bio=0.6)
    technical["status"] = "PASS_TECHNICAL_NEGATIVE" if technical["donors_defeating_null"] == 0 else "FAIL_TECHNICAL_NEGATIVE"
    clean["status"] = "PASS_CLEAN_NEGATIVE" if clean["donors_defeating_null"] == 0 else "FAIL_CLEAN_NEGATIVE"
    planted["status"] = "PASS_PLANTED_POSITIVE" if planted["donors_defeating_null"] >= 7 else "FAIL_PLANTED_POSITIVE"
    passed = technical["status"].startswith("PASS") and clean["status"].startswith("PASS") and planted["status"].startswith("PASS")
    return {
        "schema": "JEPA_TD_R1_DEPTH_MATCHED_NULL_QUALIFICATION_V2",
        "status": "PASS_R1_DEPTH_MATCHED_NULL_KNOWN_TRUTH" if passed else "FAIL_R1_DEPTH_MATCHED_NULL_KNOWN_TRUTH",
        "seed": seed,
        "worlds": {
            "TECHNICAL_LIBRARY_SIZE_ONLY": technical,
            "CLEAN_NEGATIVE": clean,
            "PLANTED_RELATIONAL_BIOLOGY": planted,
        },
        "contract": null_contract(),
        "human_r1_adjudication_authorized": False,
        "authority": dict(NO_AUTHORITY),
    }
