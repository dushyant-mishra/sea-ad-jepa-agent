#!/usr/bin/env python3
"""V21 production-authority hardening wrapper.

This module restores the complete pre-hardening authority surface and adds the
post-review bindings that were accidentally lost in 9f98320f.  The historical
implementation is kept byte-exact in t0_v21_authority_pre_hardening_v1.py so the
repair is auditable.  Effect transport remains OPEN: receipts can be sealed and
validated for review, but no production power verdict can be returned.
"""
from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import numpy as np

import t0_v21_authority_pre_hardening_v1 as _core

STOP = _core.STOP
TRANSPORT_STOP = "STOP_T0_V21_EFFECT_TRANSPORT_NOT_AUTHORITY_BOUND"
EFFECT_TRANSPORT_STATUS = "OPEN"
POWER_GATE_PRODUCTION_VERDICT_CAPABILITY = "DISABLED"

KIND = _core.KIND
PERM_KIND = _core.PERM_KIND
DESIGN_KIND = _core.DESIGN_KIND
GEOMETRY_KIND = _core.GEOMETRY_KIND
CALIBRATION_KIND = _core.CALIBRATION_KIND
N_DISCOVERY = _core.N_DISCOVERY
N_CONFIRMATION = _core.N_CONFIRMATION
ALPHA = _core.ALPHA
TARGET_POWER = _core.TARGET_POWER
FROZEN_PERMUTATIONS = _core.FROZEN_PERMUTATIONS
PROTECTED_ROLES = _core.PROTECTED_ROLES
ALLOWED_CONFIRMATION_DESIGN_SOURCES = _core.ALLOWED_CONFIRMATION_DESIGN_SOURCES
ALLOWED_GEOMETRY_TRANSPORT_MODES = _core.ALLOWED_GEOMETRY_TRANSPORT_MODES
FORBIDDEN_GEOMETRY_TRANSPORT_MODES = _core.FORBIDDEN_GEOMETRY_TRANSPORT_MODES
AUTHORITY_FIELDS = _core.AUTHORITY_FIELDS
FOLD_FIELDS = _core.FOLD_FIELDS
CALIBRATION_FIELDS = _core.CALIBRATION_FIELDS

# These names are permitted only as receipt labels while transport is OPEN.
# They are not transport authority.  Production verdict capability remains
# disabled independently of the label supplied by a caller.
ALLOWED_EFFECT_ESTIMANDS = frozenset({
    "whole_pipeline_permutation_standardized_effect_v1",
    "prospective_conservative_geometry_envelope_effect_v1",
})
TRANSPORT_AUTHORIZED_EFFECT_ESTIMANDS = frozenset()
FORBIDDEN_EFFECT_ESTIMAND_TOKENS = frozenset({
    "hc3", "t_over_sqrt_n", "t/sqrt(n)", "assembled_hc3",
})

canonical_digest = _core.canonical_digest
validate_source_authority = _core.validate_source_authority
seal_confirmation_design_receipt = _core.seal_confirmation_design_receipt
validate_confirmation_design_receipt = _core.validate_confirmation_design_receipt
seal_predictor_geometry_transport_receipt = _core.seal_predictor_geometry_transport_receipt


def _fail(message: str) -> None:
    raise RuntimeError(f"{STOP}: {message}")


def _require_hex_digest(name: str, value: Any) -> str:
    return _core._require_hex_digest(name, value)


def _validate_ridge_metadata(cross_fit_artifact: Mapping[str, Any]) -> None:
    folds = tuple(cross_fit_artifact.get("folds", ()))
    if len(folds) != N_DISCOVERY:
        _fail("cross-fit folds must carry exactly 28 outer folds")
    observed: list[float | None] = []
    for fold in folds:
        value = fold.get("fold_ridge_exponent") if isinstance(fold, Mapping) else None
        if value is None:
            observed.append(None)
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            _fail("fold_ridge_exponent must be numeric when present")
        if not math.isfinite(number):
            _fail("fold_ridge_exponent must be finite when present")
        observed.append(number)

    declared = cross_fit_artifact.get("fold_ridge_exponents")
    if not isinstance(declared, Sequence) or isinstance(declared, (str, bytes)) or len(declared) != N_DISCOVERY:
        _fail("cross-fit fold_ridge_exponents must carry exactly 28 entries")
    for got, want in zip(declared, observed, strict=True):
        if want is None:
            if got is None:
                continue
            _fail("fold_ridge_exponents claims a value not present in the corresponding fold")
        try:
            got_num = float(got)
        except (TypeError, ValueError):
            _fail("cross-fit fold_ridge_exponents must be numeric or null")
        if not math.isfinite(got_num) or got_num != want:
            _fail("cross-fit fold_ridge_exponents does not match the per-fold records")

    recorded = all(v is not None for v in observed)
    vary = recorded and len({float(v) for v in observed if v is not None}) > 1
    if cross_fit_artifact.get("fold_ridge_exponents_recorded") is not recorded:
        _fail("cross-fit fold_ridge_exponents_recorded does not match the fold records")
    if cross_fit_artifact.get("fold_ridge_exponents_vary") is not vary:
        _fail("cross-fit fold_ridge_exponents_vary does not match the fold records")


def seal_authoritative_crossfit(*, cross_fit_artifact: Mapping[str, Any],
                                source_authority: Mapping[str, Any],
                                fold_provenance: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    _validate_ridge_metadata(cross_fit_artifact)
    return _core.seal_authoritative_crossfit(
        cross_fit_artifact=cross_fit_artifact,
        source_authority=source_authority,
        fold_provenance=fold_provenance,
    )


def validate_authoritative_crossfit(artifact: Mapping[str, Any], *,
                                    expected_source_authority: Mapping[str, Any]) -> dict[str, Any]:
    result = _core.validate_authoritative_crossfit(
        artifact, expected_source_authority=expected_source_authority)
    _validate_ridge_metadata(artifact.get("cross_fit_artifact", {}))
    return result


def _permutation_behavior() -> dict[str, Any]:
    return {
        "permutation_scope": "at8_across_donors",
        "donor_ordering": "frozen",
        "observation_table_row_order": "frozen",
        "nuisance_design_rebuilt_each_shuffle": True,
        "standardization_recomputed_each_shuffle": True,
        "complete_fit_repeated_each_shuffle": True,
        "nuisance_signature_included_each_shuffle": True,
        "preserves_nans": True,
        "preserves_iteration_cap_stopping": True,
        "shuffled_full_residualized_refit": True,
        "shuffled_noise_sampling": True,
        "permutations": FROZEN_PERMUTATIONS,
    }


def nested_permutation_null_digest() -> str:
    return canonical_digest(_permutation_behavior(), domain="T0_V21_NESTED_PERMUTATION_NULL_V1")


def seal_nested_permutation_evidence(*, authoritative_crossfit_digest: str,
                                     source_authority_digest: str,
                                     nested_pipeline_code_sha: str,
                                     contract_sha: str,
                                     n_permutations: int,
                                     seed: int,
                                     p_upper: float,
                                     null_digest: str | None = None) -> dict[str, Any]:
    # null_digest is retained for API compatibility but is not trusted; the seal
    # derives the behavioral-null digest from the frozen procedure itself.
    base = _core.seal_nested_permutation_evidence(
        authoritative_crossfit_digest=authoritative_crossfit_digest,
        source_authority_digest=source_authority_digest,
        nested_pipeline_code_sha=nested_pipeline_code_sha,
        contract_sha=contract_sha,
        n_permutations=n_permutations,
        seed=seed,
        p_upper=p_upper,
        null_digest=nested_permutation_null_digest(),
    )
    body = {k: v for k, v in base.items() if k != "evidence_digest"}
    body.update(_permutation_behavior())
    body["null_digest"] = nested_permutation_null_digest()
    body["evidence_digest"] = canonical_digest(body, domain="T0_V21_NESTED_PERMUTATION_EVIDENCE_V1")
    return body


def validate_nested_permutation_evidence(evidence: Mapping[str, Any], *,
                                         artifact_digest: str,
                                         source_authority_digest: str,
                                         expected_pipeline_code_sha: str,
                                         expected_contract_sha: str,
                                         expected_evidence_digest: str) -> dict[str, Any]:
    if not isinstance(evidence, Mapping) or evidence.get("kind") != PERM_KIND:
        _fail("matching nested-permutation evidence is required")
    expected_evidence_digest = _require_hex_digest("expected_evidence_digest", expected_evidence_digest)
    if evidence.get("evidence_digest") != expected_evidence_digest:
        _fail("nested-permutation evidence is not the externally expected receipt")
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
        **_permutation_behavior(),
    }
    for key, expected in checks.items():
        if evidence.get(key) != expected:
            if key == "shuffled_full_residualized_refit":
                _fail("nested permutation must repeat the shuffled complete residualized refit")
            _fail(f"nested-permutation evidence mismatch for {key}")
    if evidence.get("null_digest") != nested_permutation_null_digest():
        _fail("nested-permutation null digest does not bind the frozen behavioral procedure")
    p = float(evidence.get("p_upper", float("nan")))
    if not math.isfinite(p) or not (0.0 < p <= ALPHA):
        _fail("nested discovery permutation test does not reject at frozen alpha")
    return {"verified": True, "evidence_digest": evidence["evidence_digest"], "p_upper": p}


def validate_predictor_geometry_transport_receipt(receipt: Mapping[str, Any], *,
                                                  artifact_digest: str,
                                                  source_authority_digest: str,
                                                  confirmation_design_receipt_digest: str,
                                                  expected_contract_sha: str,
                                                  expected_receipt_digest: str) -> dict[str, Any]:
    expected_receipt_digest = _require_hex_digest("expected_receipt_digest", expected_receipt_digest)
    if receipt.get("receipt_digest") != expected_receipt_digest:
        _fail("predictor-geometry transport receipt is not the externally expected receipt")
    return _core.validate_predictor_geometry_transport_receipt(
        receipt,
        artifact_digest=artifact_digest,
        source_authority_digest=source_authority_digest,
        confirmation_design_receipt_digest=confirmation_design_receipt_digest,
        expected_contract_sha=expected_contract_sha,
    )


def _validate_effect_estimand(effect_estimand: str) -> str:
    value = str(effect_estimand)
    lower = value.lower()
    if value not in ALLOWED_EFFECT_ESTIMANDS or any(token in lower for token in FORBIDDEN_EFFECT_ESTIMAND_TOKENS):
        _fail("effect_estimand is not an enumerated non-HC3 calibration label")
    return value


def seal_power_calibration_receipt(**kwargs: Any) -> dict[str, Any]:
    kwargs = dict(kwargs)
    kwargs["effect_estimand"] = _validate_effect_estimand(kwargs.get("effect_estimand", ""))
    return _core.seal_power_calibration_receipt(**kwargs)


def validate_power_calibration_receipt(receipt: Mapping[str, Any], *,
                                       artifact_digest: str,
                                       source_authority_digest: str,
                                       nested_permutation_evidence_digest: str,
                                       confirmation_design_receipt_digest: str,
                                       predictor_geometry_transport_digest: str,
                                       expected_calibration_code_sha: str,
                                       expected_contract_sha: str,
                                       expected_calibration_receipt_digest: str) -> dict[str, Any]:
    expected_calibration_receipt_digest = _require_hex_digest(
        "expected_calibration_receipt_digest", expected_calibration_receipt_digest)
    if receipt.get("receipt_digest") != expected_calibration_receipt_digest:
        _fail("power calibration receipt is not the externally expected receipt")
    _validate_effect_estimand(str(receipt.get("effect_estimand", "")))
    return _core.validate_power_calibration_receipt(
        receipt,
        artifact_digest=artifact_digest,
        source_authority_digest=source_authority_digest,
        nested_permutation_evidence_digest=nested_permutation_evidence_digest,
        confirmation_design_receipt_digest=confirmation_design_receipt_digest,
        predictor_geometry_transport_digest=predictor_geometry_transport_digest,
        expected_calibration_code_sha=expected_calibration_code_sha,
        expected_contract_sha=expected_contract_sha,
    )


def decision_capable_power_gate(*, artifact: Mapping[str, Any],
                                expected_source_authority: Mapping[str, Any],
                                permutation_evidence: Mapping[str, Any],
                                expected_nested_pipeline_code_sha: str,
                                expected_nested_permutation_evidence_digest: str,
                                confirmation_design_receipt: Mapping[str, Any],
                                expected_confirmation_design_receipt_digest: str,
                                predictor_geometry_transport_receipt: Mapping[str, Any],
                                expected_predictor_geometry_transport_digest: str,
                                power_calibration_receipt: Mapping[str, Any],
                                expected_power_calibration_receipt_digest: str,
                                expected_calibration_code_sha: str) -> dict[str, Any]:
    verified = validate_authoritative_crossfit(
        artifact, expected_source_authority=expected_source_authority)
    expected_contract = str(expected_source_authority["contract_sha"])
    perm = validate_nested_permutation_evidence(
        permutation_evidence,
        artifact_digest=verified["artifact_digest"],
        source_authority_digest=verified["source_authority_digest"],
        expected_pipeline_code_sha=expected_nested_pipeline_code_sha,
        expected_contract_sha=expected_contract,
        expected_evidence_digest=expected_nested_permutation_evidence_digest,
    )
    design = validate_confirmation_design_receipt(
        confirmation_design_receipt,
        expected_contract_sha=expected_contract,
        expected_receipt_digest=expected_confirmation_design_receipt_digest,
    )
    geometry = validate_predictor_geometry_transport_receipt(
        predictor_geometry_transport_receipt,
        artifact_digest=verified["artifact_digest"],
        source_authority_digest=verified["source_authority_digest"],
        confirmation_design_receipt_digest=design["receipt_digest"],
        expected_contract_sha=expected_contract,
        expected_receipt_digest=expected_predictor_geometry_transport_digest,
    )
    validate_power_calibration_receipt(
        power_calibration_receipt,
        artifact_digest=verified["artifact_digest"],
        source_authority_digest=verified["source_authority_digest"],
        nested_permutation_evidence_digest=perm["evidence_digest"],
        confirmation_design_receipt_digest=design["receipt_digest"],
        predictor_geometry_transport_digest=geometry["receipt_digest"],
        expected_calibration_code_sha=expected_calibration_code_sha,
        expected_contract_sha=expected_contract,
        expected_calibration_receipt_digest=expected_power_calibration_receipt_digest,
    )
    # Receipt validity is necessary but not sufficient.  The owner-controlled
    # module status is the only re-enable point; caller arguments cannot override it.
    if EFFECT_TRANSPORT_STATUS != "CLOSED":
        raise RuntimeError(f"{TRANSPORT_STOP}: effect transport is {EFFECT_TRANSPORT_STATUS}")
    raise RuntimeError(f"{TRANSPORT_STOP}: no transport-authorized effect estimand is frozen")
