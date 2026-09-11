#!/usr/bin/env python3
"""Fail-closed V21 authority successor.

The last green V1 authority implementation is preserved byte-for-byte in
`t0_v21_authority_legacy_v1.py`.  This module is the active compatibility
surface.  It restores that implementation, adds executor-level cross-fit
revalidation (including ridge metadata), requires externally expected receipt
digests, and disables every production power verdict while effect transport is
not authority-bound.

Design repair is not implementation qualification: documenting an open
transport problem is insufficient if another authority entry point can still
return `clears_gate=True`.  Therefore the production gate and production power
calibration receipts fail closed at module level while transport is OPEN.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from t0_v21_authority_legacy_v1 import *  # noqa: F401,F403
import t0_v21_authority_legacy_v1 as _legacy
import t0_v21_selection_and_power_v1 as _executor

STOP_TRANSPORT = "STOP_T0_V21_EFFECT_TRANSPORT_NOT_AUTHORITY_BOUND"
EFFECT_TRANSPORT_STATUS = "OPEN"

# These names are deliberately *not* authority today.  They are recorded so a
# future change cannot quietly promote one by string convention alone.
UNVALIDATED_EFFECT_ESTIMANDS = frozenset({
    "assembled_hc3_t_over_sqrt_n",
    "whole_pipeline_permutation_standardized_effect_v1",
    "prospective_conservative_geometry_envelope_effect_v1",
    "observed_null_sd_correction",
    "measured_null_spread_rescaling",
})


def _transport_fail(message: str) -> None:
    raise RuntimeError(f"{STOP_TRANSPORT}: {message}")


def _require_expected_digest(label: str, recorded: Any, expected: Any) -> str:
    expected_hex = _legacy._require_hex_digest(f"expected_{label}", expected)
    if str(recorded) != expected_hex:
        raise RuntimeError(
            f"{_legacy.STOP}: {label} is not the externally expected receipt")
    return expected_hex


def seal_authoritative_crossfit(*, cross_fit_artifact: Mapping[str, Any],
                                source_authority: Mapping[str, Any],
                                fold_provenance: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Seal only an executor-verified cross-fit artifact.

    The executor's canonical verifier derives ridge metadata from all 28 folds
    and compares it with the artifact's declared metadata before recomputing the
    artifact digest.  This closes the self-consistent-metadata substitution that
    the truncated 9f98320f implementation attempted to address.
    """
    _executor.verify_cross_fit_artifact(dict(cross_fit_artifact))
    _legacy.validate_source_authority(source_authority, source_authority)
    return _legacy.seal_authoritative_crossfit(
        cross_fit_artifact=cross_fit_artifact,
        source_authority=source_authority,
        fold_provenance=fold_provenance,
    )


def validate_authoritative_crossfit(artifact: Mapping[str, Any], *,
                                    expected_source_authority: Mapping[str, Any]) -> dict[str, Any]:
    checked = _legacy.validate_authoritative_crossfit(
        artifact, expected_source_authority=expected_source_authority)
    executor_checked = _executor.verify_cross_fit_artifact(
        dict(artifact.get("cross_fit_artifact", {})))
    return checked | {
        "executor_crossfit_revalidated": True,
        "executor_crossfit_digest": executor_checked["artifact_digest"],
    }


def validate_nested_permutation_evidence(evidence: Mapping[str, Any], *,
                                         artifact_digest: str,
                                         source_authority_digest: str,
                                         expected_pipeline_code_sha: str,
                                         expected_contract_sha: str,
                                         expected_evidence_digest: str) -> dict[str, Any]:
    _require_expected_digest(
        "nested-permutation evidence digest",
        evidence.get("evidence_digest"),
        expected_evidence_digest,
    )
    return _legacy.validate_nested_permutation_evidence(
        evidence,
        artifact_digest=artifact_digest,
        source_authority_digest=source_authority_digest,
        expected_pipeline_code_sha=expected_pipeline_code_sha,
        expected_contract_sha=expected_contract_sha,
    )


def validate_predictor_geometry_transport_receipt(receipt: Mapping[str, Any], *,
                                                  artifact_digest: str,
                                                  source_authority_digest: str,
                                                  confirmation_design_receipt_digest: str,
                                                  expected_contract_sha: str,
                                                  expected_receipt_digest: str) -> dict[str, Any]:
    _require_expected_digest(
        "predictor-geometry transport receipt digest",
        receipt.get("receipt_digest"),
        expected_receipt_digest,
    )
    return _legacy.validate_predictor_geometry_transport_receipt(
        receipt,
        artifact_digest=artifact_digest,
        source_authority_digest=source_authority_digest,
        confirmation_design_receipt_digest=confirmation_design_receipt_digest,
        expected_contract_sha=expected_contract_sha,
    )


def seal_power_calibration_receipt(*args: Any, **kwargs: Any) -> dict[str, Any]:
    estimand = str(kwargs.get("effect_estimand", ""))
    if EFFECT_TRANSPORT_STATUS != "CLOSED":
        _transport_fail(
            f"effect estimand {estimand!r} is not authority-bound while transport is OPEN")
    if estimand in UNVALIDATED_EFFECT_ESTIMANDS or not estimand:
        _transport_fail(f"effect estimand {estimand!r} is not authority-bound")
    return _legacy.seal_power_calibration_receipt(*args, **kwargs)


def validate_power_calibration_receipt(receipt: Mapping[str, Any], *,
                                       artifact_digest: str,
                                       source_authority_digest: str,
                                       nested_permutation_evidence_digest: str,
                                       confirmation_design_receipt_digest: str,
                                       predictor_geometry_transport_digest: str,
                                       expected_calibration_code_sha: str,
                                       expected_contract_sha: str,
                                       expected_calibration_receipt_digest: str) -> dict[str, Any]:
    _require_expected_digest(
        "power calibration receipt digest",
        receipt.get("receipt_digest"),
        expected_calibration_receipt_digest,
    )
    if EFFECT_TRANSPORT_STATUS != "CLOSED":
        _transport_fail("production power calibration is disabled while transport is OPEN")
    estimand = str(receipt.get("effect_estimand", ""))
    if estimand in UNVALIDATED_EFFECT_ESTIMANDS or not estimand:
        _transport_fail(f"effect estimand {estimand!r} is not authority-bound")
    return _legacy.validate_power_calibration_receipt(
        receipt,
        artifact_digest=artifact_digest,
        source_authority_digest=source_authority_digest,
        nested_permutation_evidence_digest=nested_permutation_evidence_digest,
        confirmation_design_receipt_digest=confirmation_design_receipt_digest,
        predictor_geometry_transport_digest=predictor_geometry_transport_digest,
        expected_calibration_code_sha=expected_calibration_code_sha,
        expected_contract_sha=expected_contract_sha,
    )


def decision_capable_power_gate(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Production verdict capability is disabled until transport is closed.

    This refusal is intentionally independent of caller-supplied receipts.  A
    well-formed receipt cannot re-enable a module whose owner-approved transport
    status is OPEN.
    """
    _transport_fail(
        "effect transport remains OPEN; no V21 production power verdict may be emitted")
