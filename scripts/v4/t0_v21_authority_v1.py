#!/usr/bin/env python3
"""Fail-closed V21 authority successor.

The last green V1 authority source is preserved byte-for-byte beside this module
as `t0_v21_authority_legacy_v1.py.txt`.  It is evidence, not an importable
production authority path.  This module loads that historical implementation
into a private namespace only to reuse already-reviewed sealing/validation
mechanics, then selectively exposes the safe surface.

The active surface additionally revalidates the nested cross-fit with the
current executor (which derives and binds ridge metadata), requires externally
expected receipt digests, and disables production power calibration and verdicts
while effect transport is not authority-bound.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

import t0_v21_selection_and_power_v1 as _executor

_LEGACY_PATH = Path(__file__).with_name("t0_v21_authority_legacy_v1.py.txt")
if not _LEGACY_PATH.is_file():
    raise RuntimeError("STOP_T0_V21_AUTHORITY_NOT_VALID: preserved green authority source is missing")
_legacy_ns: dict[str, Any] = {
    "__name__": "_t0_v21_authority_preserved_green_v1",
    "__file__": str(_LEGACY_PATH),
}
exec(compile(_LEGACY_PATH.read_text(encoding="utf-8"), str(_LEGACY_PATH), "exec"), _legacy_ns)

# Explicitly export the reviewed non-power primitives.  Do not export the old
# decision_capable_power_gate or old power receipt constructors/validators.
STOP = _legacy_ns["STOP"]
KIND = _legacy_ns["KIND"]
PERM_KIND = _legacy_ns["PERM_KIND"]
DESIGN_KIND = _legacy_ns["DESIGN_KIND"]
GEOMETRY_KIND = _legacy_ns["GEOMETRY_KIND"]
CALIBRATION_KIND = _legacy_ns["CALIBRATION_KIND"]
N_DISCOVERY = _legacy_ns["N_DISCOVERY"]
N_CONFIRMATION = _legacy_ns["N_CONFIRMATION"]
ALPHA = _legacy_ns["ALPHA"]
TARGET_POWER = _legacy_ns["TARGET_POWER"]
FROZEN_PERMUTATIONS = _legacy_ns["FROZEN_PERMUTATIONS"]
PROTECTED_ROLES = _legacy_ns["PROTECTED_ROLES"]
ALLOWED_CONFIRMATION_DESIGN_SOURCES = _legacy_ns["ALLOWED_CONFIRMATION_DESIGN_SOURCES"]
ALLOWED_GEOMETRY_TRANSPORT_MODES = _legacy_ns["ALLOWED_GEOMETRY_TRANSPORT_MODES"]
FORBIDDEN_GEOMETRY_TRANSPORT_MODES = _legacy_ns["FORBIDDEN_GEOMETRY_TRANSPORT_MODES"]
AUTHORITY_FIELDS = _legacy_ns["AUTHORITY_FIELDS"]
FOLD_FIELDS = _legacy_ns["FOLD_FIELDS"]
CALIBRATION_FIELDS = _legacy_ns["CALIBRATION_FIELDS"]
canonical_digest = _legacy_ns["canonical_digest"]
validate_source_authority = _legacy_ns["validate_source_authority"]
seal_nested_permutation_evidence = _legacy_ns["seal_nested_permutation_evidence"]
seal_confirmation_design_receipt = _legacy_ns["seal_confirmation_design_receipt"]
validate_confirmation_design_receipt = _legacy_ns["validate_confirmation_design_receipt"]
seal_predictor_geometry_transport_receipt = _legacy_ns["seal_predictor_geometry_transport_receipt"]

_legacy_seal_authoritative_crossfit = _legacy_ns["seal_authoritative_crossfit"]
_legacy_validate_authoritative_crossfit = _legacy_ns["validate_authoritative_crossfit"]
_legacy_validate_nested_permutation_evidence = _legacy_ns["validate_nested_permutation_evidence"]
_legacy_validate_predictor_geometry_transport_receipt = _legacy_ns["validate_predictor_geometry_transport_receipt"]
_legacy_seal_power_calibration_receipt = _legacy_ns["seal_power_calibration_receipt"]
_legacy_validate_power_calibration_receipt = _legacy_ns["validate_power_calibration_receipt"]
_legacy_require_hex_digest = _legacy_ns["_require_hex_digest"]
# The historical decision gate is intentionally discarded rather than retained
# under a private alias: there must be one normal authority path, and it is the
# fail-closed function defined below.
_legacy_ns.pop("decision_capable_power_gate", None)
del _legacy_ns

STOP_TRANSPORT = "STOP_T0_V21_EFFECT_TRANSPORT_NOT_AUTHORITY_BOUND"
EFFECT_TRANSPORT_STATUS = "OPEN"

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
    expected_hex = _legacy_require_hex_digest(f"expected_{label}", expected)
    if str(recorded) != expected_hex:
        raise RuntimeError(f"{STOP}: {label} is not the externally expected receipt")
    return expected_hex


def seal_authoritative_crossfit(*, cross_fit_artifact: Mapping[str, Any],
                                source_authority: Mapping[str, Any],
                                fold_provenance: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Seal only a cross-fit that passes the executor's canonical verifier."""
    _executor.verify_cross_fit_artifact(dict(cross_fit_artifact))
    validate_source_authority(source_authority, source_authority)
    return _legacy_seal_authoritative_crossfit(
        cross_fit_artifact=cross_fit_artifact,
        source_authority=source_authority,
        fold_provenance=fold_provenance,
    )


def validate_authoritative_crossfit(artifact: Mapping[str, Any], *,
                                    expected_source_authority: Mapping[str, Any]) -> dict[str, Any]:
    checked = _legacy_validate_authoritative_crossfit(
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
    return _legacy_validate_nested_permutation_evidence(
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
    return _legacy_validate_predictor_geometry_transport_receipt(
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
    return _legacy_seal_power_calibration_receipt(*args, **kwargs)


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
    return _legacy_validate_power_calibration_receipt(
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
    """No production power verdict exists while effect transport is OPEN."""
    _transport_fail(
        "effect transport remains OPEN; no V21 production power verdict may be emitted")
