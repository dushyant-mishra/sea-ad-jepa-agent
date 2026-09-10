from __future__ import annotations

"""Separately versioned T0 V20 replay-equivalence verifier.

This module does not alter the frozen V20 bit-exact verifier. It defines a
second, explicit equivalence policy for cross-numeric-stack replay after exact
input provenance has matched. The budgets are frozen from the documented
cross-stack discrepancies recorded in T0_V20_REPRODUCIBILITY_FINDINGS.md.
"""

from typing import Any
import math
import numpy as np


class ReplayEquivalenceError(ValueError):
    pass


# Next-decade envelopes above the documented maxima. These are deliberately
# field-specific rather than one global np.allclose rule.
FLOAT_POLICY = {
    "beta": {"rtol": 1e-11, "atol": 1e-20, "documented_max_rtol": 2.8e-12, "documented_max_atol": 5.9e-21},
    "sigma": {"rtol": 1e-14, "atol": 1e-15, "documented_max_rtol": 8.2e-16, "documented_max_atol": 2.2e-16},
    "cv_mse_by_multiplier": {"rtol": 1e-14, "atol": 0.0, "documented_max_rtol": 2.6e-15},
}
ULP_POLICY = {"final_lambda": 1, "response_residual_sd": 1}
EXACT_ARRAY_FIELDS = (
    "mu", "decision_gene_mask", "multiplier_exponents", "canonical_donor_order",
)
EXACT_SCALAR_FIELDS = (
    "selected_multiplier_index", "selected_multiplier_exponent",
    "final_trace_scale", "discovery_age_center",
)
STATE_PRIMARY_FLOAT_RTOL = 1e-12
STATE_PRIMARY_FLOAT_ATOL = 0.0
STATE_PRIMARY_FLOAT_FIELDS = ("beta", "hc3_se", "t_observed")
STATE_PRIMARY_EXACT_FIELDS = (
    "estimable", "n", "null_t", "p_full", "p_lower", "p_reduced", "p_upper",
    "permutations", "residual_df",
)


def _fail(field: str, detail: str) -> None:
    raise ReplayEquivalenceError(f"T0 replay-equivalence mismatch: {field}: {detail}")


def _require_same_keys(a: dict[str, Any], b: dict[str, Any], where: str) -> None:
    if set(a) != set(b):
        missing = sorted(set(a) - set(b))
        extra = sorted(set(b) - set(a))
        _fail(where, f"key set differs; missing={missing}, extra={extra}")


def _as_finite_float_array(x: Any, field: str) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    if not np.isfinite(arr).all():
        _fail(field, "all compared floating values must be finite")
    return arr


def _float_metrics(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    diff = np.abs(a - b)
    max_abs = float(diff.max(initial=0.0))
    denom = np.maximum(np.abs(a), np.abs(b))
    rel = np.zeros_like(diff, dtype=np.float64)
    nz = denom > 0
    rel[nz] = diff[nz] / denom[nz]
    max_rel = float(rel.max(initial=0.0))
    return max_abs, max_rel


def _check_tolerant_array(field: str, av: Any, bv: Any, policy: dict[str, float]) -> dict[str, float]:
    a = _as_finite_float_array(av, field)
    b = _as_finite_float_array(bv, field)
    if a.shape != b.shape:
        _fail(field, f"shape differs: {a.shape} != {b.shape}")
    diff = np.abs(a - b)
    scale = np.maximum(np.abs(a), np.abs(b))
    allowed = policy["atol"] + policy["rtol"] * scale
    if not np.all(diff <= allowed):
        max_abs, max_rel = _float_metrics(a, b)
        _fail(field, f"outside frozen budget; max_abs={max_abs:.17g}, max_rel={max_rel:.17g}")
    max_abs, max_rel = _float_metrics(a, b)
    return {"max_abs": max_abs, "max_rel": max_rel}


def _check_one_ulp(field: str, av: Any, bv: Any) -> int:
    a = float(av); b = float(bv)
    if not math.isfinite(a) or not math.isfinite(b):
        _fail(field, "both values must be finite")
    if a == b:
        return 0
    if b == float(np.nextafter(np.float64(a), np.float64(np.inf))) or b == float(np.nextafter(np.float64(a), np.float64(-np.inf))):
        return 1
    _fail(field, f"more than one float64 ULP apart: {a!r} vs {b!r}")
    raise AssertionError("unreachable")


def compare_fit_equivalence(frozen_fit: dict[str, Any], recomputed_fit: dict[str, Any]) -> dict[str, Any]:
    _require_same_keys(frozen_fit, recomputed_fit, "fit")
    observed = {}
    for field, policy in FLOAT_POLICY.items():
        observed[field] = _check_tolerant_array(field, frozen_fit[field], recomputed_fit[field], policy)
    for field in EXACT_ARRAY_FIELDS:
        if not np.array_equal(np.asarray(frozen_fit[field]), np.asarray(recomputed_fit[field])):
            _fail(field, "exact array equality required")
    ulps = {}
    for field, max_ulp in ULP_POLICY.items():
        distance = _check_one_ulp(field, frozen_fit[field], recomputed_fit[field])
        if distance > max_ulp:
            _fail(field, f"ULP distance {distance} > {max_ulp}")
        ulps[field] = distance
    for field in EXACT_SCALAR_FIELDS:
        if frozen_fit[field] != recomputed_fit[field]:
            _fail(field, "exact scalar equality required")
    return {
        "equivalent": True,
        "schema": "JEPA_T0_V20_TARGET_REPLAY_EQUIVALENCE_V1",
        "float_policy": FLOAT_POLICY,
        "ulp_policy": ULP_POLICY,
        "exact_array_fields": list(EXACT_ARRAY_FIELDS),
        "exact_scalar_fields": list(EXACT_SCALAR_FIELDS),
        "observed": observed,
        "observed_ulp_distance": ulps,
    }


def compare_decision_equivalence(committed: dict[str, Any], recomputed: dict[str, Any]) -> dict[str, Any]:
    for terminal in ("state_terminal", "tail_terminal"):
        if committed.get(terminal) != recomputed.get(terminal):
            _fail(terminal, f"exact terminal required: {committed.get(terminal)!r} != {recomputed.get(terminal)!r}")
    a = committed.get("state_primary")
    b = recomputed.get("state_primary")
    if not isinstance(a, dict) or not isinstance(b, dict):
        _fail("state_primary", "both records must contain a state_primary object")
    _require_same_keys(a, b, "state_primary")
    observed = {}
    for field in STATE_PRIMARY_FLOAT_FIELDS:
        av = float(a[field]); bv = float(b[field])
        if not math.isfinite(av) or not math.isfinite(bv):
            _fail(f"state_primary.{field}", "both values must be finite")
        if not math.isclose(av, bv, rel_tol=STATE_PRIMARY_FLOAT_RTOL, abs_tol=STATE_PRIMARY_FLOAT_ATOL):
            rel = abs(av-bv) / max(abs(av), abs(bv)) if max(abs(av), abs(bv)) else 0.0
            _fail(f"state_primary.{field}", f"outside frozen rtol; relative difference={rel:.17g}")
        rel = abs(av-bv) / max(abs(av), abs(bv)) if max(abs(av), abs(bv)) else 0.0
        observed[field] = {"abs": abs(av-bv), "rel": rel}
    for field in STATE_PRIMARY_EXACT_FIELDS:
        if a[field] != b[field]:
            _fail(f"state_primary.{field}", "exact equality required")
    return {
        "equivalent": True,
        "schema": "JEPA_T0_V20_DECISION_REPLAY_EQUIVALENCE_V1",
        "state_primary_float_rtol": STATE_PRIMARY_FLOAT_RTOL,
        "state_primary_float_atol": STATE_PRIMARY_FLOAT_ATOL,
        "state_primary_float_fields": list(STATE_PRIMARY_FLOAT_FIELDS),
        "state_primary_exact_fields": list(STATE_PRIMARY_EXACT_FIELDS),
        "observed": observed,
        "terminals_exact": True,
    }


def verify_target_v2_replay_equivalent(target_dir, **kwargs: Any) -> dict[str, Any]:
    """Recompute the frozen target with exact provenance, then apply V1 equivalence.

    The historical `verify_target_v2_against_raw` remains untouched and retains
    its bit-exact semantics. This function is an opt-in successor verifier.
    """
    import t0_stage2a_pre_at8_gate_v1 as stage2a

    frozen_mod = stage2a._frozen("t0_discovery_fit_v2")
    frozen = frozen_mod.load_target_v2(target_dir, kwargs["feature_split_csv"])
    recomputed = frozen_mod.fit_discovery_target_v2(**kwargs)
    if frozen["provenance"] != recomputed["provenance"]:
        _fail("provenance", "exact canonical raw discovery provenance mismatch")
    report = compare_fit_equivalence(frozen["fit"], recomputed["fit"])
    return {
        "verified": True,
        "equivalence_schema": report["schema"],
        "package_root_sha256": frozen["package_root_sha256"],
        "discovery_provenance_root": frozen["provenance"]["root_sha256"],
        "equivalence_report": report,
    }
