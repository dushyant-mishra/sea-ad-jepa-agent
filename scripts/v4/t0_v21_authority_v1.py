#!/usr/bin/env python3
"""Fail-closed production authority for the V21 decision path.

This module intentionally wraps, rather than rewrites, the numerical V21 executor.
A self-consistent score artifact is not sufficient production evidence: callers must
also present externally expected source/model authority, fold-level provenance,
whole-pipeline nested-permutation evidence, a prospectively approved confirmation-
design receipt, predictor-geometry transport authority, and a geometry-aware power
calibration receipt.  Protected reader partitions are never valid calibration-
design sources, and the historical iid-normal surrogate calibration is not a
production decision path.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping, Sequence

import numpy as np

STOP = "STOP_T0_V21_AUTHORITY_NOT_VALID"
KIND = "t0_v21_authoritative_crossfit_v1"
PERM_KIND = "t0_v21_nested_permutation_evidence_v1"
DESIGN_KIND = "t0_v21_confirmation_design_receipt_v1"
GEOMETRY_KIND = "t0_v21_predictor_geometry_transport_receipt_v1"
CALIBRATION_KIND = "t0_v21_power_calibration_receipt_v1"
N_DISCOVERY = 28
N_CONFIRMATION = 12
ALPHA = 0.025
TARGET_POWER = 0.80
FROZEN_PERMUTATIONS = 9999
PROTECTED_ROLES = frozenset({"reader_validation", "reader_oracle", "protected_partition"})
ALLOWED_CONFIRMATION_DESIGN_SOURCES = frozenset({
    "discovery_only_design_envelope",
    "pre_unblinding_demographics_authority",
})
ALLOWED_GEOMETRY_TRANSPORT_MODES = frozenset({
    "actual_discovery_residualized_score_geometry",
    "prospective_conservative_geometry_envelope",
})
FORBIDDEN_GEOMETRY_TRANSPORT_MODES = frozenset({
    "iid_normal_surrogate",
    "random_normal_surrogate",
    "representative_synthetic_design",
})

ALLOWED_EFFECT_ESTIMANDS = frozenset({
    # Production-calibration receipts may only name estimands whose scale is
    # anchored by whole-pipeline permutation or a prospective conservative
    # geometry envelope.  The assembled HC3 `t/sqrt(n)` quantity remains
    # disallowed until a transport derivation exists.
    "whole_pipeline_permutation_standardized_effect_v1",
    "prospective_conservative_geometry_envelope_effect_v1",
})
FORBIDDEN_EFFECT_ESTIMAND_TOKENS = frozenset({
    "hc3",
    "t_over_sqrt_n",
    "t/sqrt(n)",
    "assembled_hc3",
})
AUTHORITY_FIELDS = (
    "expression_root_digest",
    "donor_role_ledger_digest",
    "donor_order_digest",
    "molecular_address_digest",
    "transformation_digest",
    "nuisance_spec_digest",
    "estimator_id",
    "target_code_sha",
    "contract_sha",
)
FOLD_FIELDS = (
    "held_out_donor_id",
    "train_donor_ids",
    "training_data_digest",
    "ridge_trace_digest",
    "fitted_target_digest",
    "prediction",
)
CALIBRATION_FIELDS = (
    "kind",
    "authoritative_crossfit_digest",
    "source_authority_digest",
    "nested_permutation_evidence_digest",
    "confirmation_design_receipt_digest",
    "predictor_geometry_transport_digest",
    "calibration_code_sha",
    "contract_sha",
    "n_simulations",
    "n_permutations",
    "seed",
    "alpha",
    "target_power",
    "power",
    "monte_carlo_standard_error",
    "power_lower_95",
    "clears_gate",
    "consumes_predictor_geometry",
    "uses_iid_normal_surrogate",
    "effect_estimand",
)


def _fail(message: str) -> None:
    raise RuntimeError(f"{STOP}: {message}")


def _plain(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Mapping):
        return {str(k): _plain(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (tuple, list)):
        return [_plain(v) for v in value]
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            _fail("nonfinite value cannot be hashed")
        return value
    _fail(f"unsupported canonical value type {type(value).__name__}")


def canonical_digest(value: Any, *, domain: str) -> str:
    payload = json.dumps(_plain(value), sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(domain.encode("ascii") + b"\0" + payload).hexdigest()


def _require_hex_digest(name: str, value: Any) -> str:
    text = str(value)
    if len(text) != 64 or any(c not in "0123456789abcdef" for c in text):
        _fail(f"{name} must be a lowercase SHA-256 digest")
    return text


def _require_finite_1d(name: str, value: Any, n: int) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64)
    if arr.shape != (n,) or not np.isfinite(arr).all():
        _fail(f"{name} must be finite 1-D length {n}")
    return arr


def _require_complete_binary_sex(name: str, value: Any, n: int) -> np.ndarray:
    arr = _require_finite_1d(name, value, n)
    uniq = np.unique(arr)
    if uniq.size != 2 or not np.array_equal(uniq, np.array([0.0, 1.0])):
        _fail(f"{name} must contain complete binary 0/1 coding")
    return arr


def validate_source_authority(authority: Mapping[str, Any],
                              expected: Mapping[str, Any]) -> str:
    if not isinstance(authority, Mapping) or not isinstance(expected, Mapping):
        _fail("source authority and expected authority must be mappings")
    missing = [k for k in AUTHORITY_FIELDS if k not in authority]
    expected_missing = [k for k in AUTHORITY_FIELDS if k not in expected]
    if missing or expected_missing:
        _fail(f"source authority fields missing: artifact={missing}, expected={expected_missing}")
    extra = sorted(set(authority) - set(AUTHORITY_FIELDS))
    if extra:
        _fail(f"unexpected source-authority fields {extra}")
    for field in AUTHORITY_FIELDS:
        if str(authority[field]) != str(expected[field]):
            _fail(f"source authority mismatch for {field}")
    for field in AUTHORITY_FIELDS:
        if field.endswith("_digest") or field.endswith("_sha"):
            _require_hex_digest(field, authority[field])
    return canonical_digest(dict(authority), domain="T0_V21_SOURCE_AUTHORITY_V1")


def _validate_legacy_crossfit_structure(cross_fit_artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Revalidate the legacy/sealed cross-fit structure before any production use.

    A matching digest alone only proves byte stability.  Production authority must
    also prove the bytes encode exactly the 28-fold leave-one-donor-out structure
    with valid donor-level arrays and score/fold agreement.
    """
    if not isinstance(cross_fit_artifact, Mapping):
        _fail("cross-fit artifact must be a mapping")
    if cross_fit_artifact.get("kind") != "t0_v21_cross_fit_artifact_v1":
        _fail("cross-fit artifact kind is not t0_v21_cross_fit_artifact_v1")
    if int(cross_fit_artifact.get("n_donors", -1)) != N_DISCOVERY:
        _fail("cross-fit artifact must declare exactly 28 discovery donors")

    donor_ids = tuple(str(x) for x in cross_fit_artifact.get("donor_ids", ()))
    if len(donor_ids) != N_DISCOVERY or len(set(donor_ids)) != N_DISCOVERY:
        _fail("cross-fit must carry exactly 28 unique donor identifiers")
    y = _require_finite_1d("cross_fit.y", cross_fit_artifact.get("y", ()), N_DISCOVERY)
    age = _require_finite_1d("cross_fit.age", cross_fit_artifact.get("age", ()), N_DISCOVERY)
    sex = _require_complete_binary_sex("cross_fit.sex", cross_fit_artifact.get("sex", ()), N_DISCOVERY)

    scores = _require_finite_1d("cross_fit.scores", cross_fit_artifact.get("scores", ()), N_DISCOVERY)
    folds = cross_fit_artifact.get("folds")
    if not isinstance(folds, Sequence) or len(folds) != N_DISCOVERY:
        _fail("cross-fit folds must carry exactly 28 outer folds")

    by_donor = {}
    fold_ridge_exponents: list[float | None] = []
    for fold in folds:
        if not isinstance(fold, Mapping):
            _fail("each cross-fit fold must be a mapping")
        held_out = str(fold.get("held_out_donor_id", ""))
        if not held_out or held_out in by_donor:
            _fail("cross-fit folds must have exactly one fold per donor")
        train = tuple(str(x) for x in fold.get("train_donor_ids", ()))
        if len(train) != N_DISCOVERY - 1 or held_out in train or set(train) | {held_out} != set(donor_ids):
            _fail("each cross-fit fold must train on exactly the other 27 discovery donors")
        for field in FOLD_FIELDS:
            if field not in fold:
                _fail(f"cross-fit fold {held_out} missing {field}")
        for digest_field in ("training_data_digest", "ridge_trace_digest", "fitted_target_digest"):
            _require_hex_digest(f"fold[{held_out}].{digest_field}", fold[digest_field])
        pred = float(fold["prediction"])
        if not math.isfinite(pred):
            _fail("cross-fit predictions must be finite")
        ridge_exponent = fold.get("fold_ridge_exponent")
        if ridge_exponent is None:
            fold_ridge_exponents.append(None)
        else:
            try:
                ridge_exponent_num = float(ridge_exponent)
            except (TypeError, ValueError):
                _fail("fold_ridge_exponent must be numeric when present")
            if not math.isfinite(ridge_exponent_num):
                _fail("fold_ridge_exponent must be finite when present")
            fold_ridge_exponents.append(ridge_exponent_num)
        by_donor[held_out] = pred

    if set(by_donor) != set(donor_ids):
        _fail("cross-fit held-out donor set must exactly match donor_ids")
    for_fold_ridge = cross_fit_artifact.get("fold_ridge_exponents")
    if not isinstance(for_fold_ridge, Sequence) or len(for_fold_ridge) != N_DISCOVERY:
        _fail("cross-fit fold_ridge_exponents must carry exactly 28 entries")
    for declared, observed in zip(for_fold_ridge, fold_ridge_exponents, strict=True):
        if observed is None:
            if declared is Note:
                continue
            _fail("cross-fit fold_ridge_exponents claims a value not present in the corresponding fold")
        try:
            declared_num = float(declared)
        except (TypeError, ValueError):
            _fail("cross-fit fold_ridge_exponents must be numeric or null")
        if not math.isfinite(declared_num) or declared_num != observed:
            _fail("cross-fit fold_ridge_exponents does not match the per-fold records")
    recorded = all(v is not None for v in fold_ridge_exponents)
    vary = recorded and len({float(v) for v in fold_ridge_exponents if v is not None}) > 1
    if cross_fit_artifact.get("fold_ridge_exponents_recorded") is not recorded:
        _fail("cross-fit fold_ridge_exponents_recorded does not match the fold records")
    if cross_fit_artifact.get("fold_ridge_exponents_vary") is not vary:
        _fail("cross-fit fold_ridge_exponents_vary does not match the fold records")

    scores_from_folds = np.asarray([by_donor[d] for d in donor_ids], dtype=np.float64)
    if not np.array_equal(scores, scores_from_folds):
        _fail("cross-fit scores must exactly match fold predictions in donor_ids order")
    return {
        "donor_ids": donor_ids, "y": y, "age": age, "sex": sex, "scores": scores,
        "fold_ridge_exponents": tuple(fold_ridge_exponents),
        "fold_ridge_exponents_recorded": recorded,
        "fold_ridge_exponents_vary": vary,
    }


def validate_authoritative_crossfit(artifact: Mapping[str, Any], *,
                                      expected_source_authority: Mapping[str, Any]) -> dict[str, Any]:
    authority_digest = validate_source_authority(artifact.get("source_authority", 
                                                                 {}),
                                                expected=expected_source_authority)
    validated = _validate_legacy_crossfit_structure(artifact)
    artifact_digest = canonical_digest(artifact, domain="T0_V21_AUTHORITATIVE_CROSSFIT_V1")
    return {"artifact_digest": artifact_digest, "source_authority_digest": authority_digest,
            "donor_ids": validated["donor_ids"], "y": validated["y"], "age": validated["age"],
            "sex": validated["sex"], "scores": validated["scores"],
            "fold_ridge_exponents": validated["fold_ridge_exponents"],
            "fold_ridge_exponents_recorded": validated["fold_ridge_exponents_recorded"],
            "fold_ridge_exponents_vary": validated["fold_ridge_exponents_vary"]}
