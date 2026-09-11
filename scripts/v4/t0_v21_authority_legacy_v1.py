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
    scores = _require_finite_1d("cross_fit.oof_scores", cross_fit_artifact.get("oof_scores", ()), N_DISCOVERY)

    folds = tuple(cross_fit_artifact.get("folds", ()))
    if len(folds) != N_DISCOVERY:
        _fail("cross-fit must carry exactly 28 fold records")
    fold_by_held: dict[int, Mapping[str, Any]] = {}
    everything = set(range(N_DISCOVERY))
    by_fold = np.empty(N_DISCOVERY, dtype=np.float64)
    for fold in folds:
        if not isinstance(fold, Mapping):
            _fail("every fold record must be a mapping")
        for key in ("held_out_index", "n_train", "train_indices", "out_of_fold_prediction"):
            if key not in fold:
                _fail(f"fold record missing {key}")
        held = int(fold["held_out_index"])
        if held < 0 or held >= N_DISCOVERY or held in fold_by_held:
            _fail("cross-fit folds must hold out indexes 0..27 exactly once")
        train = tuple(int(i) for i in fold["train_indices"])
        if int(fold["n_train"]) != N_DISCOVERY - 1:
            _fail("each cross-fit fold must declare n_train=27")
        if len(train) != N_DISCOVERY - 1 or set(train) != everything - {held}:
            _fail(f"fold {held} does not train on the exact complement of its held-out donor")
        prediction = float(fold["out_of_fold_prediction"])
        if not math.isfinite(prediction):
            _fail(f"fold {held} has a nonfinite out-of-fold prediction")
        by_fold[held] = prediction
        fold_by_held[held] = fold
    if set(fold_by_held) != everything:
        _fail("cross-fit folds must hold out indexes 0..27 exactly once")
    if not np.array_equal(scores, by_fold):
        _fail("cross-fit score vector does not match held-out-index-ordered fold predictions")
    return {
        "donor_ids": donor_ids,
        "y": y,
        "age": age,
        "sex": sex,
        "scores": scores,
        "folds": folds,
        "fold_by_held": fold_by_held,
    }


def seal_authoritative_crossfit(*, cross_fit_artifact: Mapping[str, Any],
                                source_authority: Mapping[str, Any],
                                fold_provenance: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    checked = _validate_legacy_crossfit_structure(cross_fit_artifact)
    donor_ids = checked["donor_ids"]
    scores = checked["scores"]
    folds_by_held = checked["fold_by_held"]
    if len(fold_provenance) != N_DISCOVERY:
        _fail("exactly 28 fold-provenance records are required")

    expected_donors = set(donor_ids)
    normalized = []
    seen = set()
    for record in fold_provenance:
        if not isinstance(record, Mapping):
            _fail("fold provenance records must be mappings")
        missing = [k for k in FOLD_FIELDS if k not in record]
        if missing:
            _fail(f"fold provenance missing fields {missing}")
        held = str(record["held_out_donor_id"])
        if held in seen or held not in expected_donors:
            _fail(f"invalid/duplicate held-out donor {held}")
        seen.add(held)
        held_idx = donor_ids.index(held)
        legal_train = expected_donors - {held}
        train = tuple(str(x) for x in record["train_donor_ids"])
        if len(train) != N_DISCOVERY - 1 or set(train) != legal_train:
            _fail(f"fold for {held} does not bind the exact 27-donor complement")
        old_fold = folds_by_held[held_idx]
        old_train_ids = {donor_ids[int(i)] for i in old_fold["train_indices"]}
        if old_train_ids != legal_train:
            _fail(f"underlying cross-fit fold for {held} is not the legal complement")
        prediction = float(record["prediction"])
        if not math.isfinite(prediction) or prediction != float(scores[held_idx]):
            _fail(f"fold provenance prediction mismatch for {held}")
        for name in ("training_data_digest", "ridge_trace_digest", "fitted_target_digest"):
            _require_hex_digest(name, record[name])
        normalized.append({k: _plain(record[k]) for k in FOLD_FIELDS})

    if seen != expected_donors:
        _fail("not every discovery donor has fold provenance")
    source_digest = canonical_digest(dict(source_authority), domain="T0_V21_SOURCE_AUTHORITY_V1")
    body = {
        "kind": KIND,
        "cross_fit_artifact": _plain(cross_fit_artifact),
        "source_authority": _plain(source_authority),
        "source_authority_digest": source_digest,
        "fold_provenance": sorted(normalized, key=lambda r: r["held_out_donor_id"]),
    }
    body["artifact_digest"] = canonical_digest(body, domain="T0_V21_AUTHORITATIVE_CROSSFIT_V1")
    return body


def validate_authoritative_crossfit(artifact: Mapping[str, Any],
                                    *, expected_source_authority: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(artifact, Mapping) or artifact.get("kind") != KIND:
        _fail("production decisions require t0_v21_authoritative_crossfit_v1")
    recorded = str(artifact.get("artifact_digest", ""))
    body = {k: artifact[k] for k in artifact if k != "artifact_digest"}
    recomputed = canonical_digest(body, domain="T0_V21_AUTHORITATIVE_CROSSFIT_V1")
    if recorded != recomputed:
        _fail("authoritative cross-fit digest does not recompute")
    source_digest = validate_source_authority(artifact.get("source_authority", {}),
                                              expected_source_authority)
    if artifact.get("source_authority_digest") != source_digest:
        _fail("source-authority digest mismatch")
    rebuilt = seal_authoritative_crossfit(
        cross_fit_artifact=artifact.get("cross_fit_artifact", {}),
        source_authority=artifact.get("source_authority", {}),
        fold_provenance=artifact.get("fold_provenance", ()),
    )
    if rebuilt["artifact_digest"] != recorded:
        _fail("cross-fit structure differs from sealed authority")
    return {"verified": True, "artifact_digest": recorded,
            "source_authority_digest": source_digest}


def seal_nested_permutation_evidence(*, authoritative_crossfit_digest: str,
                                     source_authority_digest: str,
                                     nested_pipeline_code_sha: str,
                                     contract_sha: str,
                                     n_permutations: int,
                                     seed: int,
                                     p_upper: float,
                                     null_digest: str) -> dict[str, Any]:
    _require_hex_digest("authoritative_crossfit_digest", authoritative_crossfit_digest)
    _require_hex_digest("source_authority_digest", source_authority_digest)
    _require_hex_digest("nested_pipeline_code_sha", nested_pipeline_code_sha)
    _require_hex_digest("contract_sha", contract_sha)
    _require_hex_digest("null_digest", null_digest)
    if int(n_permutations) != FROZEN_PERMUTATIONS:
        _fail(f"decision evidence requires frozen B={FROZEN_PERMUTATIONS}")
    p = float(p_upper)
    if not (0.0 < p <= 1.0):
        _fail("nested-permutation p_upper must lie in (0,1]")
    body = {"kind": PERM_KIND, "authoritative_crossfit_digest": authoritative_crossfit_digest,
            "source_authority_digest": source_authority_digest,
            "nested_pipeline_code_sha": nested_pipeline_code_sha,
            "contract_sha": contract_sha, "n_permutations": int(n_permutations),
            "seed": int(seed), "alpha": ALPHA, "p_upper": p,
            "null_digest": null_digest}
    body["evidence_digest"] = canonical_digest(body, domain="T0_V21_NESTED_PERMUTATION_EVIDENCE_V1")
    return body


def validate_nested_permutation_evidence(evidence: Mapping[str, Any], *,
                                         artifact_digest: str,
                                         source_authority_digest: str,
                                         expected_pipeline_code_sha: str,
                                         expected_contract_sha: str) -> dict[str, Any]:
    if not isinstance(evidence, Mapping) or evidence.get("kind") != PERM_KIND:
        _fail("matching nested-permutation evidence is required")
    body = {k: evidence[k] for k in evidence if k != "evidence_digest"}
    if evidence.get("evidence_digest") != canonical_digest(body, domain="T0_V21_NESTED_PERMUTATION_EVIDENCE_V1"):
        _fail("nested-permutation evidence digest does not recompute")
    checks = {
        "authoritative_crossfit_digest": artifact_digest,
        "source_authority_digest": source_authority_digest,
        "nested_pipeline_code_sha": expected_pipeline_code_sha,
        "contract_sha": expected_contract_sha,
        "n_permutations": FROZEN_PERMUTATIONS,
        "alpha": ALPHA,
    }
    for key, expected in checks.items():
        if str(evidence.get(key)) != str(expected):
            _fail(f"nested-permutation evidence mismatch for {key}")
    if float(evidence["p_upper"]) > ALPHA:
        _fail("nested discovery permutation test does not reject at frozen alpha")
    return {"verified": True, "evidence_digest": evidence["evidence_digest"],
            "p_upper": float(evidence["p_upper"])}


def seal_confirmation_design_receipt(*, age: Sequence[float], sex: Sequence[float],
                                     source_role: str, source_digest: str,
                                     contract_sha: str) -> dict[str, Any]:
    role = str(source_role)
    if role in PROTECTED_ROLES:
        _fail(f"protected role {role} cannot supply pre-unblinding calibration design")
    if role not in ALLOWED_CONFIRMATION_DESIGN_SOURCES:
        _fail(f"confirmation design source role {role!r} is not an approved pre-unblinding authority")
    age_arr = _require_finite_1d("confirmation age", age, N_CONFIRMATION)
    sex_arr = _require_complete_binary_sex("confirmation sex", sex, N_CONFIRMATION)
    _require_hex_digest("source_digest", source_digest)
    _require_hex_digest("contract_sha", contract_sha)
    body = {"kind": DESIGN_KIND, "source_role": role,
            "source_digest": source_digest, "contract_sha": contract_sha,
            "n": N_CONFIRMATION,
            "age_digest": canonical_digest(age_arr, domain="T0_V21_CONFIRMATION_AGE_V1"),
            "sex_digest": canonical_digest(sex_arr, domain="T0_V21_CONFIRMATION_SEX_V1")}
    body["receipt_digest"] = canonical_digest(body, domain="T0_V21_CONFIRMATION_DESIGN_RECEIPT_V1")
    return body


def validate_confirmation_design_receipt(receipt: Mapping[str, Any], *,
                                         expected_contract_sha: str,
                                         expected_receipt_digest: str,
                                         expected_source_role: str | None = None,
                                         expected_source_digest: str | None = None,
                                         age: Sequence[float] | None = None,
                                         sex: Sequence[float] | None = None) -> dict[str, Any]:
    if not isinstance(receipt, Mapping) or receipt.get("kind") != DESIGN_KIND:
        _fail("a confirmation-design receipt is required")
    role = str(receipt.get("source_role"))
    if role in PROTECTED_ROLES:
        _fail("protected reader partitions cannot supply pre-unblinding design calibration")
    if role not in ALLOWED_CONFIRMATION_DESIGN_SOURCES:
        _fail(f"confirmation design source role {role!r} is not approved")
    body = {k: receipt[k] for k in receipt if k != "receipt_digest"}
    if receipt.get("receipt_digest") != canonical_digest(body, domain="T0_V21_CONFIRMATION_DESIGN_RECEIPT_V1"):
        _fail("confirmation-design receipt digest does not recompute")
    if receipt.get("receipt_digest") != _require_hex_digest("expected_receipt_digest", expected_receipt_digest):
        _fail("confirmation-design receipt is not the externally expected design authority")
    if receipt.get("contract_sha") != expected_contract_sha:
        _fail("confirmation-design contract mismatch")
    if expected_source_role is not None and role != str(expected_source_role):
        _fail("confirmation-design source role mismatch")
    if expected_source_digest is not None and receipt.get("source_digest") != _require_hex_digest("expected_source_digest", expected_source_digest):
        _fail("confirmation-design source digest mismatch")
    if age is not None or sex is not None:
        if age is None or sex is None:
            _fail("age and sex must be supplied together if arrays are checked")
        expected_age = canonical_digest(_require_finite_1d("confirmation age", age, N_CONFIRMATION),
                                        domain="T0_V21_CONFIRMATION_AGE_V1")
        expected_sex = canonical_digest(_require_complete_binary_sex("confirmation sex", sex, N_CONFIRMATION),
                                        domain="T0_V21_CONFIRMATION_SEX_V1")
        if receipt.get("age_digest") != expected_age or receipt.get("sex_digest") != expected_sex:
            _fail("confirmation design arrays do not match their prospective receipt")
    return {"verified": True, "receipt_digest": receipt["receipt_digest"], "source_role": role}


def seal_predictor_geometry_transport_receipt(*,
                                              authoritative_crossfit_digest: str,
                                              source_authority_digest: str,
                                              confirmation_design_receipt_digest: str,
                                              contract_sha: str,
                                              transport_mode: str,
                                              residualized_predictor_geometry_digest: str,
                                              calibration_design_digest: str,
                                              assumption_statement_digest: str) -> dict[str, Any]:
    mode = str(transport_mode)
    if mode in FORBIDDEN_GEOMETRY_TRANSPORT_MODES or mode not in ALLOWED_GEOMETRY_TRANSPORT_MODES:
        _fail(f"predictor-geometry transport mode {mode!r} is not decision-capable")
    for name, value in (
        ("authoritative_crossfit_digest", authoritative_crossfit_digest),
        ("source_authority_digest", source_authority_digest),
        ("confirmation_design_receipt_digest", confirmation_design_receipt_digest),
        ("contract_sha", contract_sha),
        ("residualized_predictor_geometry_digest", residualized_predictor_geometry_digest),
        ("calibration_design_digest", calibration_design_digest),
        ("assumption_statement_digest", assumption_statement_digest),
    ):
        _require_hex_digest(name, value)
    body = {"kind": GEOMETRY_KIND,
            "authoritative_crossfit_digest": authoritative_crossfit_digest,
            "source_authority_digest": source_authority_digest,
            "confirmation_design_receipt_digest": confirmation_design_receipt_digest,
            "contract_sha": contract_sha,
            "transport_mode": mode,
            "residualized_predictor_geometry_digest": residualized_predictor_geometry_digest,
            "calibration_design_digest": calibration_design_digest,
            "assumption_statement_digest": assumption_statement_digest}
    body["receipt_digest"] = canonical_digest(body, domain="T0_V21_PREDICTOR_GEOMETRY_TRANSPORT_V1")
    return body


def validate_predictor_geometry_transport_receipt(receipt: Mapping[str, Any], *,
                                                  artifact_digest: str,
                                                  source_authority_digest: str,
                                                  confirmation_design_receipt_digest: str,
                                                  expected_contract_sha: str) -> dict[str, Any]:
    if not isinstance(receipt, Mapping) or receipt.get("kind") != GEOMETRY_KIND:
        _fail("predictor-geometry transport receipt is required")
    body = {k: receipt[k] for k in receipt if k != "receipt_digest"}
    if receipt.get("receipt_digest") != canonical_digest(body, domain="T0_V21_PREDICTOR_GEOMETRY_TRANSPORT_V1"):
        _fail("predictor-geometry transport receipt digest does not recompute")
    checks = {
        "authoritative_crossfit_digest": artifact_digest,
        "source_authority_digest": source_authority_digest,
        "confirmation_design_receipt_digest": confirmation_design_receipt_digest,
        "contract_sha": expected_contract_sha,
    }
    for key, expected in checks.items():
        if str(receipt.get(key)) != str(expected):
            _fail(f"predictor-geometry transport mismatch for {key}")
    mode = str(receipt.get("transport_mode"))
    if mode in FORBIDDEN_GEOMETRY_TRANSPORT_MODES or mode not in ALLOWED_GEOMETRY_TRANSPORT_MODES:
        _fail(f"predictor-geometry transport mode {mode!r} is not decision-capable")
    return {"verified": True, "receipt_digest": receipt["receipt_digest"], "transport_mode": mode}


def seal_power_calibration_receipt(*,
                                   authoritative_crossfit_digest: str,
                                   source_authority_digest: str,
                                   nested_permutation_evidence_digest: str,
                                   confirmation_design_receipt_digest: str,
                                   predictor_geometry_transport_digest: str,
                                   calibration_code_sha: str,
                                   contract_sha: str,
                                   n_simulations: int,
                                   n_permutations: int,
                                   seed: int,
                                   power: float,
                                   monte_carlo_standard_error: float,
                                   power_lower_95: float,
                                   clears_gate: bool,
                                   consumes_predictor_geometry: bool,
                                   uses_iid_normal_surrogate: bool,
                                   effect_estimand: str) -> dict[str, Any]:
    for name, value in (
        ("authoritative_crossfit_digest", authoritative_crossfit_digest),
        ("source_authority_digest", source_authority_digest),
        ("nested_permutation_evidence_digest", nested_permutation_evidence_digest),
        ("confirmation_design_receipt_digest", confirmation_design_receipt_digest),
        ("predictor_geometry_transport_digest", predictor_geometry_transport_digest),
        ("calibration_code_sha", calibration_code_sha),
        ("contract_sha", contract_sha),
    ):
        _require_hex_digest(name, value)
    if int(n_permutations) != FROZEN_PERMUTATIONS:
        _fail(f"power calibration requires frozen B={FROZEN_PERMUTATIONS}")
    p = float(power); se = float(monte_carlo_standard_error); lower = float(power_lower_95)
    if not (0.0 <= p <= 1.0 and 0.0 <= se and 0.0 <= lower <= 1.0):
        _fail("power, standard error, and lower limit must be finite probabilities")
    expected_lower = max(0.0, p - 1.96 * se)
    if abs(lower - expected_lower) > 1e-12:
        _fail("power_lower_95 must equal max(0, power - 1.96*se)")
    if bool(clears_gate) != bool(lower >= TARGET_POWER):
        _fail("clears_gate must be determined by the lower Monte Carlo limit")
    if not bool(consumes_predictor_geometry):
        _fail("calibration must consume predictor-geometry transport authority")
    if bool(uses_iid_normal_surrogate):
        _fail("iid-normal surrogate calibration is not decision-capable")
    body = {"kind": CALIBRATION_KIND,
            "authoritative_crossfit_digest": authoritative_crossfit_digest,
            "source_authority_digest": source_authority_digest,
            "nested_permutation_evidence_digest": nested_permutation_evidence_digest,
            "confirmation_design_receipt_digest": confirmation_design_receipt_digest,
            "predictor_geometry_transport_digest": predictor_geometry_transport_digest,
            "calibration_code_sha": calibration_code_sha,
            "contract_sha": contract_sha,
            "n_simulations": int(n_simulations),
            "n_permutations": int(n_permutations),
            "seed": int(seed),
            "alpha": ALPHA,
            "target_power": TARGET_POWER,
            "power": p,
            "monte_carlo_standard_error": se,
            "power_lower_95": lower,
            "clears_gate": bool(clears_gate),
            "consumes_predictor_geometry": True,
            "uses_iid_normal_surrogate": False,
            "effect_estimand": str(effect_estimand)}
    body["receipt_digest"] = canonical_digest(body, domain="T0_V21_POWER_CALIBRATION_RECEIPT_V1")
    return body


def validate_power_calibration_receipt(receipt: Mapping[str, Any], *,
                                       artifact_digest: str,
                                       source_authority_digest: str,
                                       nested_permutation_evidence_digest: str,
                                       confirmation_design_receipt_digest: str,
                                       predictor_geometry_transport_digest: str,
                                       expected_calibration_code_sha: str,
                                       expected_contract_sha: str) -> dict[str, Any]:
    if not isinstance(receipt, Mapping) or receipt.get("kind") != CALIBRATION_KIND:
        _fail("geometry-aware power calibration receipt is required")
    missing = [k for k in CALIBRATION_FIELDS if k not in receipt]
    if missing:
        _fail(f"power calibration receipt missing {missing}")
    body = {k: receipt[k] for k in receipt if k != "receipt_digest"}
    if receipt.get("receipt_digest") != canonical_digest(body, domain="T0_V21_POWER_CALIBRATION_RECEIPT_V1"):
        _fail("power calibration receipt digest does not recompute")
    checks = {
        "authoritative_crossfit_digest": artifact_digest,
        "source_authority_digest": source_authority_digest,
        "nested_permutation_evidence_digest": nested_permutation_evidence_digest,
        "confirmation_design_receipt_digest": confirmation_design_receipt_digest,
        "predictor_geometry_transport_digest": predictor_geometry_transport_digest,
        "calibration_code_sha": expected_calibration_code_sha,
        "contract_sha": expected_contract_sha,
        "n_permutations": FROZEN_PERMUTATIONS,
        "alpha": ALPHA,
        "target_power": TARGET_POWER,
    }
    for key, expected in checks.items():
        if str(receipt.get(key)) != str(expected):
            _fail(f"power calibration receipt mismatch for {key}")
    return seal_power_calibration_receipt(
        authoritative_crossfit_digest=receipt["authoritative_crossfit_digest"],
        source_authority_digest=receipt["source_authority_digest"],
        nested_permutation_evidence_digest=receipt["nested_permutation_evidence_digest"],
        confirmation_design_receipt_digest=receipt["confirmation_design_receipt_digest"],
        predictor_geometry_transport_digest=receipt["predictor_geometry_transport_digest"],
        calibration_code_sha=receipt["calibration_code_sha"],
        contract_sha=receipt["contract_sha"],
        n_simulations=int(receipt["n_simulations"]),
        n_permutations=int(receipt["n_permutations"]),
        seed=int(receipt["seed"]),
        power=float(receipt["power"]),
        monte_carlo_standard_error=float(receipt["monte_carlo_standard_error"]),
        power_lower_95=float(receipt["power_lower_95"]),
        clears_gate=bool(receipt["clears_gate"]),
        consumes_predictor_geometry=bool(receipt["consumes_predictor_geometry"]),
        uses_iid_normal_surrogate=bool(receipt["uses_iid_normal_surrogate"]),
        effect_estimand=str(receipt["effect_estimand"]),
    ) | {"verified": True}


def decision_capable_power_gate(*, artifact: Mapping[str, Any],
                                expected_source_authority: Mapping[str, Any],
                                permutation_evidence: Mapping[str, Any],
                                expected_nested_pipeline_code_sha: str,
                                confirmation_design_receipt: Mapping[str, Any],
                                expected_confirmation_design_receipt_digest: str,
                                predictor_geometry_transport_receipt: Mapping[str, Any],
                                power_calibration_receipt: Mapping[str, Any],
                                expected_calibration_code_sha: str) -> dict[str, Any]:
    """Only production-authoritative V21 power entry point.

    This is deliberately receipt-based.  It does **not** call the legacy numerical
    `power_gate`, because that code still uses a random-normal surrogate predictor
    geometry.  A production decision must consume a separate calibration receipt
    that binds the approved confirmation-design authority and the predictor-
    geometry transport authority.
    """
    verified = validate_authoritative_crossfit(artifact,
                                                expected_source_authority=expected_source_authority)
    expected_contract = str(expected_source_authority["contract_sha"])
    perm = validate_nested_permutation_evidence(
        permutation_evidence, artifact_digest=verified["artifact_digest"],
        source_authority_digest=verified["source_authority_digest"],
        expected_pipeline_code_sha=expected_nested_pipeline_code_sha,
        expected_contract_sha=expected_contract)
    design = validate_confirmation_design_receipt(
        confirmation_design_receipt,
        expected_contract_sha=expected_contract,
        expected_receipt_digest=expected_confirmation_design_receipt_digest)
    geometry = validate_predictor_geometry_transport_receipt(
        predictor_geometry_transport_receipt,
        artifact_digest=verified["artifact_digest"],
        source_authority_digest=verified["source_authority_digest"],
        confirmation_design_receipt_digest=design["receipt_digest"],
        expected_contract_sha=expected_contract)
    calibration = validate_power_calibration_receipt(
        power_calibration_receipt,
        artifact_digest=verified["artifact_digest"],
        source_authority_digest=verified["source_authority_digest"],
        nested_permutation_evidence_digest=perm["evidence_digest"],
        confirmation_design_receipt_digest=design["receipt_digest"],
        predictor_geometry_transport_digest=geometry["receipt_digest"],
        expected_calibration_code_sha=expected_calibration_code_sha,
        expected_contract_sha=expected_contract)
    return {"production_authority": {"crossfit": verified, "permutation": perm,
                                      "confirmation_design": design,
                                      "predictor_geometry": geometry,
                                      "calibration": calibration},
            "clears_gate": bool(calibration["clears_gate"]),
            "power_lower_95": float(calibration["power_lower_95"])}
